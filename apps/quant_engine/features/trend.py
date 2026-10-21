"""
Trend Analysis Module.

Implements EMA trend structure (20, 50, 200 EMA), distances, slopes,
and Wilder's Average Directional Index (ADX) trend-strength regimes.
"""
from typing import Dict, Literal, Optional, Tuple
import numpy as np
from .data_quality import safe_float, safe_div


def compute_ema(series: np.ndarray, period: int) -> np.ndarray:
    """Calculates exponential moving average for a 1D array."""
    if len(series) == 0:
        return np.array([])
    alpha = 2.0 / (period + 1.0)
    ema = np.empty_like(series, dtype=float)
    ema[0] = series[0]
    for i in range(1, len(series)):
        ema[i] = alpha * series[i] + (1.0 - alpha) * ema[i - 1]
    return ema


def compute_adx(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 14,
) -> float:
    """
    Computes Wilder's Average Directional Index (ADX).
    ADX measures trend strength independent of direction [0-100].
    """
    n = len(closes)
    if n < period + 2:
        return 20.0  # Baseline neutral

    tr = np.zeros(n)
    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)

    for i in range(1, n):
        h_diff = highs[i] - highs[i - 1]
        l_diff = lows[i - 1] - lows[i]

        plus_dm[i] = h_diff if (h_diff > l_diff and h_diff > 0) else 0.0
        minus_dm[i] = l_diff if (l_diff > h_diff and l_diff > 0) else 0.0

        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )

    # Wilder smoothing
    atr_smooth = np.zeros(n)
    plus_di_smooth = np.zeros(n)
    minus_di_smooth = np.zeros(n)

    if n <= period:
        return 20.0

    atr_smooth[period] = np.sum(tr[1:period + 1])
    plus_di_smooth[period] = np.sum(plus_dm[1:period + 1])
    minus_di_smooth[period] = np.sum(minus_dm[1:period + 1])

    for i in range(period + 1, n):
        atr_smooth[i] = atr_smooth[i - 1] - (atr_smooth[i - 1] / period) + tr[i]
        plus_di_smooth[i] = plus_di_smooth[i - 1] - (plus_di_smooth[i - 1] / period) + plus_dm[i]
        minus_di_smooth[i] = minus_di_smooth[i - 1] - (minus_di_smooth[i - 1] / period) + minus_dm[i]

    dx = np.zeros(n)
    for i in range(period, n):
        p_di = safe_div(plus_di_smooth[i] * 100.0, atr_smooth[i], default=0.0)
        m_di = safe_div(minus_di_smooth[i] * 100.0, atr_smooth[i], default=0.0)
        di_sum = p_di + m_di
        dx[i] = safe_div(abs(p_di - m_di) * 100.0, di_sum, default=0.0)

    # Smooth DX to get ADX
    adx_start = period * 2
    if n <= adx_start:
        return safe_float(float(np.mean(dx[period:])), default=20.0, round_digits=1)

    adx = float(np.mean(dx[period:adx_start]))
    for i in range(adx_start, n):
        adx = ((adx * (period - 1)) + dx[i]) / period

    return safe_float(adx, default=20.0, round_digits=1)


def calculate_trend_features(
    prices: np.ndarray,
    highs: Optional[np.ndarray] = None,
    lows: Optional[np.ndarray] = None,
    period_fast: int = 20,
    period_medium: int = 50,
    period_slow: int = 200,
    adx_period: int = 14,
) -> Dict:
    """
    Calculates EMA structure, distances, slopes, ADX, and overall trend state.
    """
    last_price = safe_float(prices[-1]) if len(prices) > 0 else 0.0

    # Calculate EMAs
    ema20_series = compute_ema(prices, period_fast)
    ema50_series = compute_ema(prices, period_medium)
    ema200_series = compute_ema(prices, period_slow)

    ema20 = float(ema20_series[-1]) if len(ema20_series) > 0 else last_price
    ema50 = float(ema50_series[-1]) if len(ema50_series) > 0 else last_price
    ema200 = float(ema200_series[-1]) if len(ema200_series) > 0 else last_price

    # Distances %
    dist_ema20 = safe_div(last_price - ema20, ema20) * 100.0
    dist_ema50 = safe_div(last_price - ema50, ema50) * 100.0
    dist_ema200 = safe_div(last_price - ema200, ema200) * 100.0

    # EMA ordering
    if ema20 > ema50 > ema200 and last_price >= ema20:
        ema_structure: Literal["bullish", "bearish", "neutral"] = "bullish"
    elif ema20 < ema50 < ema200 and last_price <= ema20:
        ema_structure = "bearish"
    else:
        ema_structure = "neutral"

    # EMA slope (short-term)
    if len(ema20_series) >= 3:
        slope_delta = (ema20_series[-1] - ema20_series[-3]) / max(ema20_series[-3], 0.001)
        if slope_delta > 0.001:
            ema_slope: Literal["positive", "negative", "flat"] = "positive"
        elif slope_delta < -0.001:
            ema_slope = "negative"
        else:
            ema_slope = "flat"
    else:
        ema_slope = "flat"

    # ADX calculation
    if highs is not None and lows is not None and len(highs) == len(prices):
        adx_val = compute_adx(highs, lows, prices, period=adx_period)
    else:
        # Fallback ADX estimate from close prices
        synth_highs = prices * 1.005
        synth_lows = prices * 0.995
        adx_val = compute_adx(synth_highs, synth_lows, prices, period=adx_period)

    # Classify composite trend state
    is_trending = adx_val >= 25.0
    if ema_structure == "bullish":
        trend_state = "strong_bullish" if is_trending else "weak_bullish"
    elif ema_structure == "bearish":
        trend_state = "strong_bearish" if is_trending else "weak_bearish"
    else:
        if dist_ema20 > 1.0 and ema_slope == "positive":
            trend_state = "weak_bullish"
        elif dist_ema20 < -1.0 and ema_slope == "negative":
            trend_state = "weak_bearish"
        else:
            trend_state = "ranging"

    return {
        "ema_structure": ema_structure,
        "ema_slope": ema_slope,
        "adx": safe_float(adx_val, round_digits=1),
        "trend_state": trend_state,
        "dist_ema20_pct": safe_float(dist_ema20, round_digits=2),
        "dist_ema50_pct": safe_float(dist_ema50, round_digits=2),
        "dist_ema200_pct": safe_float(dist_ema200, round_digits=2),
    }
