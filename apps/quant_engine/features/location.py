"""
Price Location & Market Position Module.

Calculates rolling high-low range position (20D, 60D) and percentage distances
from key structural reference levels (recent high, recent low, VWAP, major EMAs).
"""
from typing import Dict, Optional
import numpy as np
from .data_quality import safe_float, safe_div


def calculate_range_position(prices: np.ndarray, window: int = 20) -> float:
    """
    Position inside recent high-low range [0 - 100%].
    Position = (Price - Low) / (High - Low) * 100
    """
    if len(prices) == 0:
        return 50.0
    sub = prices[-min(len(prices), window):]
    low_val = float(np.min(sub))
    high_val = float(np.max(sub))
    rng = high_val - low_val
    if rng <= 0.0:
        return 50.0
    pos = (float(prices[-1]) - low_val) / rng * 100.0
    return safe_float(np.clip(pos, 0.0, 100.0), round_digits=1)


def calculate_location_features(
    prices: np.ndarray,
    highs: Optional[np.ndarray] = None,
    lows: Optional[np.ndarray] = None,
    vwap: Optional[float] = None,
    window_short: int = 20,
    window_medium: int = 60,
) -> Dict:
    """
    Calculates range position across 20D and 60D windows, plus distances to recent extremes.
    """
    n = len(prices)
    last_price = safe_float(prices[-1]) if n > 0 else 0.0

    h_arr = highs if highs is not None and len(highs) == n else prices
    l_arr = lows if lows is not None and len(lows) == n else prices

    # 20D Range
    sub_h20 = h_arr[-min(n, window_short):]
    sub_l20 = l_arr[-min(n, window_short):]
    high_20d = float(np.max(sub_h20)) if len(sub_h20) > 0 else last_price
    low_20d = float(np.min(sub_l20)) if len(sub_l20) > 0 else last_price
    rng_20d = high_20d - low_20d
    range_pos_20d = safe_div(last_price - low_20d, rng_20d, default=0.5) * 100.0

    # 60D Range
    sub_h60 = h_arr[-min(n, window_medium):]
    sub_l60 = l_arr[-min(n, window_medium):]
    high_60d = float(np.max(sub_h60)) if len(sub_h60) > 0 else last_price
    low_60d = float(np.min(sub_l60)) if len(sub_l60) > 0 else last_price
    rng_60d = high_60d - low_60d
    range_pos_60d = safe_div(last_price - low_60d, rng_60d, default=0.5) * 100.0

    # Distances to 20D high & low
    dist_high_pct = safe_div(high_20d - last_price, last_price, default=0.0) * 100.0
    dist_low_pct = safe_div(last_price - low_20d, last_price, default=0.0) * 100.0

    # Dist to VWAP if provided
    dist_vwap_pct = safe_div(last_price - vwap, vwap, default=0.0) * 100.0 if vwap else 0.0

    return {
        "range_position_20d": safe_float(np.clip(range_pos_20d, 0.0, 100.0), round_digits=1),
        "range_position_60d": safe_float(np.clip(range_pos_60d, 0.0, 100.0), round_digits=1),
        "nearest_resistance": safe_float(high_20d, round_digits=2),
        "nearest_support": safe_float(low_20d, round_digits=2),
        "dist_nearest_resistance_pct": safe_float(dist_high_pct, round_digits=2),
        "dist_nearest_support_pct": safe_float(-dist_low_pct, round_digits=2),
        "dist_vwap_pct": safe_float(dist_vwap_pct, round_digits=2),
    }
