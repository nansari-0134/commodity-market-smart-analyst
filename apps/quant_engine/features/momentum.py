"""
Momentum Analysis Module.

Implements Wilder's RSI (value, percentile, state, direction)
and Appel's MACD (line, signal, histogram, direction, crossovers).
"""
from typing import Dict, Literal
import numpy as np
from .data_quality import safe_float, safe_div
from .trend import compute_ema


def compute_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Computes Wilder's Relative Strength Index (RSI) across the price series.
    Returns 1D array of RSI values [0-100].
    """
    n = len(prices)
    if n < period + 1:
        return np.full(n, 50.0)

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    rsi = np.full(n, 50.0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    if avg_loss == 0.0:
        rsi[period] = 100.0 if avg_gain > 0 else 50.0
    else:
        rs = avg_gain / avg_loss
        rsi[period] = 100.0 - (100.0 / (1.0 + rs))

    for i in range(period + 1, n):
        gain = gains[i - 1]
        loss = losses[i - 1]
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period

        if avg_loss == 0.0:
            rsi[i] = 100.0 if avg_gain > 0 else 50.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))

    return rsi


def compute_macd(
    prices: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Dict[str, np.ndarray]:
    """Computes MACD line, signal line, and histogram series."""
    n = len(prices)
    if n < slow_period:
        zeros = np.zeros(n)
        return {"macd": zeros, "signal": zeros, "hist": zeros}

    fast_ema = compute_ema(prices, fast_period)
    slow_ema = compute_ema(prices, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = compute_ema(macd_line, signal_period)
    hist = macd_line - signal_line

    return {"macd": macd_line, "signal": signal_line, "hist": hist}


def calculate_momentum_features(
    prices: np.ndarray,
    rsi_period: int = 14,
    rsi_history_window: int = 60,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
) -> Dict:
    """
    Computes comprehensive momentum metrics: RSI, MACD, and momentum states.
    """
    if len(prices) < 2:
        return {
            "rsi": 50.0,
            "rsi_percentile": 50.0,
            "rsi_direction": "flat",
            "macd": 0.0,
            "macd_signal": 0.0,
            "macd_histogram": 0.0,
            "histogram_direction": "flat",
            "momentum_state": "neutral",
        }

    # RSI
    rsi_series = compute_rsi(prices, period=rsi_period)
    latest_rsi = float(rsi_series[-1])

    # RSI percentile rank over 60D
    rsi_window = rsi_series[-min(len(rsi_series), rsi_history_window):]
    rsi_percentile = float(np.mean(rsi_window <= latest_rsi) * 100.0)

    # RSI Direction (last 3 periods)
    if len(rsi_series) >= 4:
        rsi_delta = latest_rsi - rsi_series[-4]
        if rsi_delta > 1.5:
            rsi_direction: Literal["rising", "falling", "flat"] = "rising"
        elif rsi_delta < -1.5:
            rsi_direction = "falling"
        else:
            rsi_direction = "flat"
    else:
        rsi_direction = "flat"

    # MACD
    macd_dict = compute_macd(prices, fast_period=macd_fast, slow_period=macd_slow, signal_period=macd_signal)
    latest_macd = float(macd_dict["macd"][-1])
    latest_signal = float(macd_dict["signal"][-1])
    latest_hist = float(macd_dict["hist"][-1])

    # Histogram direction
    if len(macd_dict["hist"]) >= 3:
        hist_delta = latest_hist - macd_dict["hist"][-3]
        if hist_delta > 0.01:
            hist_direction: Literal["increasing", "decreasing", "flat"] = "increasing"
        elif hist_delta < -0.01:
            hist_direction = "decreasing"
        else:
            hist_direction = "flat"
    else:
        hist_direction = "flat"

    # Momentum State
    if latest_rsi >= 70.0:
        momentum_state = "overbought"
    elif latest_rsi <= 30.0:
        momentum_state = "oversold"
    elif (rsi_direction == "rising" and hist_direction == "increasing") or (latest_hist > 0 and hist_direction == "increasing"):
        momentum_state = "strengthening"
    elif (rsi_direction == "falling" and hist_direction == "decreasing") or (latest_hist < 0 and hist_direction == "decreasing"):
        momentum_state = "weakening"
    else:
        momentum_state = "neutral"

    return {
        "rsi": safe_float(latest_rsi, round_digits=1),
        "rsi_percentile": safe_float(rsi_percentile, round_digits=1),
        "rsi_direction": rsi_direction,
        "macd": safe_float(latest_macd, round_digits=3),
        "macd_signal": safe_float(latest_signal, round_digits=3),
        "macd_histogram": safe_float(latest_hist, round_digits=3),
        "histogram_direction": hist_direction,
        "momentum_state": momentum_state,
    }
