"""
VWAP & Market Location Module.

Calculates Volume-Weighted Average Price (VWAP) and percentage deviation.
"""
from typing import Dict, Optional
import numpy as np
from .data_quality import safe_float, safe_div


def compute_vwap(
    prices: np.ndarray,
    volumes: np.ndarray,
    highs: Optional[np.ndarray] = None,
    lows: Optional[np.ndarray] = None,
    window: int = 20,
) -> float:
    """
    Computes rolling Volume-Weighted Average Price (VWAP).
    Typical Price = (High + Low + Close) / 3
    VWAP = Sum(TP * Vol) / Sum(Vol)
    """
    n = len(prices)
    if n == 0:
        return 0.0

    sub_p = prices[-min(n, window):]
    sub_v = volumes[-min(n, window):] if (volumes is not None and len(volumes) == n) else np.ones(len(sub_p))

    if highs is not None and lows is not None and len(highs) == n and len(lows) == n:
        sub_h = highs[-min(n, window):]
        sub_l = lows[-min(n, window):]
        tp = (sub_h + sub_l + sub_p) / 3.0
    else:
        tp = sub_p

    total_vol = float(np.sum(sub_v))
    if total_vol <= 0:
        return float(np.mean(tp))

    vwap = float(np.sum(tp * sub_v)) / total_vol
    return vwap


def calculate_vwap_features(
    prices: np.ndarray,
    volumes: np.ndarray,
    highs: Optional[np.ndarray] = None,
    lows: Optional[np.ndarray] = None,
    window: int = 20,
) -> Dict:
    """
    Calculates VWAP and percentage deviation from current price.
    """
    if len(prices) == 0:
        return {"vwap": 0.0, "vwap_deviation_pct": 0.0}

    last_price = safe_float(prices[-1])
    vwap_val = compute_vwap(prices, volumes, highs, lows, window=window)
    dev_pct = safe_div(last_price - vwap_val, vwap_val, default=0.0) * 100.0

    return {
        "vwap": safe_float(vwap_val, round_digits=2),
        "vwap_deviation_pct": safe_float(dev_pct, round_digits=2),
    }
