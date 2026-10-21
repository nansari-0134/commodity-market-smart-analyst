"""
Price & Return Analysis Module.

Calculates multi-horizon returns, log returns, return acceleration,
and rolling historical price percentiles.
"""
from typing import Dict, Optional
import numpy as np
from .data_quality import safe_float, safe_div


def calculate_price_features(
    prices: np.ndarray,
    intraday_returns: Optional[Dict[str, float]] = None,
    lookback_window: int = 20,
) -> Dict[str, float]:
    """
    Computes price returns, acceleration, percentile rank, and Z-score.
    
    Args:
        prices: 1D array of historical settlement/close prices ending at current price.
        intraday_returns: Optional dict with '1m', '5m', '15m', '1h' percentage returns.
        lookback_window: Window size for percentile and Z-score (default: 20).
        
    Returns:
        Dict matching PriceFeatures schema.
    """
    if len(prices) == 0:
        return {
            "last": 0.0,
            "return_1m": None,
            "return_5m": None,
            "return_15m": None,
            "return_1h": None,
            "return_1d": 0.0,
            "log_return_1d": 0.0,
            "return_acceleration_1d": 0.0,
            "percentile_20d": 50.0,
            "zscore_20d": 0.0,
        }

    last_price = safe_float(prices[-1])
    
    # 1D return and log return
    ret_1d = 0.0
    log_ret_1d = 0.0
    ret_accel = 0.0
    
    if len(prices) >= 2 and prices[-2] > 0:
        prev_price = float(prices[-2])
        ret_1d = (last_price - prev_price) / prev_price
        log_ret_1d = float(np.log(last_price / prev_price))
        
        # Return acceleration: r_t - r_{t-1}
        if len(prices) >= 3 and prices[-3] > 0:
            prev_prev = float(prices[-3])
            prior_ret = (prev_price - prev_prev) / prev_prev
            ret_accel = ret_1d - prior_ret

    # Rolling window for percentile & zscore
    window = prices[-min(len(prices), lookback_window):]
    if len(window) >= 2:
        mean_val = float(np.mean(window))
        std_val = float(np.std(window, ddof=1)) if len(window) > 1 else 0.0
        zscore_20d = safe_div(last_price - mean_val, std_val, default=0.0)
        # Percentile rank: fraction of window values <= current price
        percentile_20d = float(np.mean(window <= last_price) * 100.0)
    else:
        zscore_20d = 0.0
        percentile_20d = 50.0

    # Intraday returns if supplied
    ir = intraday_returns or {}
    
    return {
        "last": last_price,
        "return_1m": safe_float(ir.get("1m")) if "1m" in ir else None,
        "return_5m": safe_float(ir.get("5m")) if "5m" in ir else None,
        "return_15m": safe_float(ir.get("15m")) if "15m" in ir else None,
        "return_1h": safe_float(ir.get("1h")) if "1h" in ir else None,
        "return_1d": safe_float(ret_1d, round_digits=6),
        "log_return_1d": safe_float(log_ret_1d, round_digits=6),
        "return_acceleration_1d": safe_float(ret_accel, round_digits=6),
        "percentile_20d": safe_float(percentile_20d, round_digits=2),
        "zscore_20d": safe_float(zscore_20d, round_digits=3),
    }
