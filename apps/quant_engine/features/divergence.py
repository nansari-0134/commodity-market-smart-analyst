"""
Generalized Divergence Detection Module.

Identifies multi-variable divergences between Price and secondary signals:
- Price vs RSI (Classic Bullish/Bearish Oscillator Divergence)
- Price vs Volume (Price advance on declining volume / Exhaustion)
- Price vs Open Interest (Smart Money Liquidation vs Speculative Chasing)
- Price vs Order Flow (Delta absorption divergence)
"""
from typing import Dict, List, Literal, Optional
import numpy as np


def detect_indicator_divergence(
    prices: np.ndarray,
    indicator: np.ndarray,
    indicator_type: Literal["price_vs_rsi", "price_vs_volume", "price_vs_oi", "price_vs_order_flow"],
    timeframe: str = "1D",
    window: int = 14,
) -> Optional[Dict]:
    """
    Detects higher-high / lower-low price divergence against a secondary indicator series.
    """
    if len(prices) < window or len(indicator) < window:
        return None

    p_sub = prices[-window:]
    i_sub = indicator[-window:]

    # Compare first half vs second half
    half = window // 2
    p_prior_peak = float(np.max(p_sub[:half]))
    p_recent_peak = float(np.max(p_sub[half:]))
    p_prior_trough = float(np.min(p_sub[:half]))
    p_recent_trough = float(np.min(p_sub[half:]))

    i_prior_peak = float(np.max(i_sub[:half]))
    i_recent_peak = float(np.max(i_sub[half:]))
    i_prior_trough = float(np.min(i_sub[:half]))
    i_recent_trough = float(np.min(i_sub[half:]))

    # Bearish Divergence: Price higher high, but Indicator lower high
    if p_recent_peak > p_prior_peak and i_recent_peak < i_prior_peak:
        p_pct = (p_recent_peak - p_prior_peak) / p_prior_peak
        i_pct = abs(i_recent_peak - i_prior_peak) / max(abs(i_prior_peak), 1.0)
        severity = "strong" if (p_pct > 0.02 and i_pct > 0.10) else ("moderate" if p_pct > 0.01 else "mild")
        return {
            "divergence_type": indicator_type,
            "direction": "bearish",
            "severity": severity,
            "timeframe": timeframe,
            "description": f"Bearish divergence: Price formed higher highs while {indicator_type.replace('price_vs_', '').upper()} formed lower highs.",
        }

    # Bullish Divergence: Price lower low, but Indicator higher low
    if p_recent_trough < p_prior_trough and i_recent_trough > i_prior_trough:
        p_pct = (p_prior_trough - p_recent_trough) / p_prior_trough
        i_pct = abs(i_recent_trough - i_prior_trough) / max(abs(i_prior_trough), 1.0)
        severity = "strong" if (p_pct > 0.02 and i_pct > 0.10) else ("moderate" if p_pct > 0.01 else "mild")
        return {
            "divergence_type": indicator_type,
            "direction": "bullish",
            "severity": severity,
            "timeframe": timeframe,
            "description": f"Bullish divergence: Price formed lower lows while {indicator_type.replace('price_vs_', '').upper()} formed higher lows.",
        }

    return None


def calculate_divergence_features(
    prices: np.ndarray,
    rsi_series: Optional[np.ndarray] = None,
    volumes: Optional[np.ndarray] = None,
    open_interest: Optional[np.ndarray] = None,
    timeframe: str = "1D",
) -> Dict:
    """
    Runs generalized divergence detection across all available indicator channels.
    """
    divergences: List[Dict] = []

    # 1. Price vs RSI
    if rsi_series is not None and len(rsi_series) == len(prices):
        div_rsi = detect_indicator_divergence(prices, rsi_series, "price_vs_rsi", timeframe=timeframe)
        if div_rsi:
            divergences.append(div_rsi)

    # 2. Price vs Volume
    if volumes is not None and len(volumes) == len(prices):
        div_vol = detect_indicator_divergence(prices, volumes, "price_vs_volume", timeframe=timeframe)
        if div_vol:
            divergences.append(div_vol)

    # 3. Price vs Open Interest
    if open_interest is not None and len(open_interest) == len(prices):
        div_oi = detect_indicator_divergence(prices, open_interest, "price_vs_oi", timeframe=timeframe)
        if div_oi:
            divergences.append(div_oi)

    return {
        "has_divergence": len(divergences) > 0,
        "active_divergences": divergences,
    }
