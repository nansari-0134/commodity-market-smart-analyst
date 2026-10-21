"""
Volatility Analysis Module.

Implements Average True Range (ATR, ATR%, ATR percentile) and
Annualized Realized Volatility (vol%, vol percentile, regime).
"""
from typing import Dict, Literal, Optional
import numpy as np
from .data_quality import safe_float, safe_div


def compute_true_range(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
) -> np.ndarray:
    """Computes True Range (TR) series for high, low, close bars."""
    n = len(closes)
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
    return tr


def compute_atr(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 14,
) -> np.ndarray:
    """Computes 14-period Wilder Average True Range series."""
    n = len(closes)
    if n == 0:
        return np.array([])
    tr = compute_true_range(highs, lows, closes)
    atr = np.zeros(n)
    if n < period:
        atr[:] = np.mean(tr)
        return atr

    atr[period - 1] = np.mean(tr[:period])
    for i in range(period, n):
        atr[i] = ((atr[i - 1] * (period - 1)) + tr[i]) / period

    return atr


def calculate_volatility_features(
    prices: np.ndarray,
    highs: Optional[np.ndarray] = None,
    lows: Optional[np.ndarray] = None,
    atr_period: int = 14,
    atr_window: int = 60,
    realized_vol_window: int = 20,
    annual_window: int = 252,
) -> Dict:
    """
    Computes ATR, ATR % of price, ATR percentile, realized volatility, and regime.
    """
    n = len(prices)
    last_price = safe_float(prices[-1]) if n > 0 else 0.0

    # Ensure Highs/Lows
    if highs is None or len(highs) != n:
        highs = prices * 1.01
    if lows is None or len(lows) != n:
        lows = prices * 0.99

    # ATR
    atr_series = compute_atr(highs, lows, prices, period=atr_period)
    latest_atr = float(atr_series[-1]) if len(atr_series) > 0 else (last_price * 0.015)
    atr_pct = safe_div(latest_atr * 100.0, last_price, default=1.5)

    # ATR Percentile over 60D
    atr_sub = atr_series[-min(len(atr_series), atr_window):]
    atr_percentile = float(np.mean(atr_sub <= latest_atr) * 100.0) if len(atr_sub) > 0 else 50.0

    # Realized Volatility (Annualized)
    if n >= 3:
        log_rets = np.diff(np.log(np.maximum(prices, 0.001)))
        roll_rets = log_rets[-min(len(log_rets), realized_vol_window):]
        daily_std = float(np.std(roll_rets, ddof=1)) if len(roll_rets) > 1 else 0.01
        realized_vol = daily_std * (252.0 ** 0.5) * 100.0

        # Percentile vs 1Y distribution
        if len(log_rets) >= 20:
            hist_vols = []
            max_look = min(len(log_rets), annual_window)
            for i in range(20, max_look + 1):
                chunk = log_rets[max(0, i - realized_vol_window):i]
                if len(chunk) > 1:
                    hist_vols.append(float(np.std(chunk, ddof=1)) * (252.0 ** 0.5) * 100.0)
            hist_arr = np.array(hist_vols)
            vol_percentile = float(np.mean(hist_arr <= realized_vol) * 100.0) if len(hist_arr) > 0 else 50.0
        else:
            vol_percentile = 50.0
    else:
        realized_vol = 25.0
        vol_percentile = 50.0

    # Volatility Regime
    if vol_percentile >= 90.0 or realized_vol >= 45.0:
        regime: Literal["low", "normal", "high", "extreme"] = "extreme"
    elif vol_percentile >= 75.0 or realized_vol >= 32.0:
        regime = "high"
    elif vol_percentile <= 25.0:
        regime = "low"
    else:
        regime = "normal"

    return {
        "atr": safe_float(latest_atr, round_digits=3),
        "atr_pct": safe_float(atr_pct, round_digits=2),
        "atr_percentile": safe_float(atr_percentile, round_digits=1),
        "realized_volatility": safe_float(realized_vol, round_digits=2),
        "vol_percentile": safe_float(vol_percentile, round_digits=1),
        "regime": regime,
    }
