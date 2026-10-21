"""
Statistical Normalization Module.

Provides rolling Z-scores, rolling empirical percentile ranks,
and robust Median Absolute Deviation (MAD) estimators.
"""
from typing import Dict, Tuple
import numpy as np
from .data_quality import safe_float, safe_div


def rolling_zscore(series: np.ndarray, window: int = 20) -> float:
    """
    Computes Z-score of the latest value relative to the rolling historical window.
    Z = (X_t - mu_t) / sigma_t
    """
    if len(series) < 2:
        return 0.0
    w = series[-min(len(series), window):]
    mean_val = float(np.mean(w))
    std_val = float(np.std(w, ddof=1)) if len(w) > 1 else 0.0
    return safe_float(safe_div(float(series[-1]) - mean_val, std_val, default=0.0), round_digits=3)


def rolling_percentile(series: np.ndarray, window: int = 20) -> float:
    """
    Computes empirical percentile rank of latest value within historical window [0 - 100].
    """
    if len(series) == 0:
        return 50.0
    w = series[-min(len(series), window):]
    val = float(series[-1])
    pct = float(np.mean(w <= val) * 100.0)
    return safe_float(pct, round_digits=2)


def robust_mad_zscore(series: np.ndarray, window: int = 20) -> float:
    """
    Computes robust Z-score using Median and Median Absolute Deviation (MAD).
    Robust Z = 0.6745 * (X_t - median) / MAD
    Resistant to extreme outlier fat tails in commodity shocks.
    """
    if len(series) < 3:
        return 0.0
    w = series[-min(len(series), window):]
    val = float(series[-1])
    median_val = float(np.median(w))
    mad_val = float(np.median(np.abs(w - median_val)))
    if mad_val == 0.0:
        return 0.0
    robust_z = 0.6745 * (val - median_val) / mad_val
    return safe_float(robust_z, round_digits=3)


def calculate_normalization_suite(
    series: np.ndarray,
    windows: Tuple[int, ...] = (20, 60, 120),
) -> Dict[str, float]:
    """
    Computes Z-scores and percentiles across multiple configurable lookback horizons.
    """
    res = {}
    for w in windows:
        res[f"zscore_{w}"] = rolling_zscore(series, window=w)
        res[f"percentile_{w}"] = rolling_percentile(series, window=w)
    return res
