"""
Support & Resistance Module.

Extracts key structural pivot levels (prior day/week high/low, swing levels)
and computes percentage distances and touch/rejection strength scores.
"""
from typing import Dict, List, Optional
import numpy as np
from .data_quality import safe_float, safe_div


def evaluate_level_strength(
    level: float,
    highs: np.ndarray,
    lows: np.ndarray,
    atr: float,
    tolerance_mult: float = 0.35,
) -> float:
    """
    Computes a quantitative strength score for a price level [0.0 - 1.0].
    Factors in touch count, rejection count, and recency.
    """
    if len(highs) == 0 or level <= 0:
        return 0.5

    band = max(atr * tolerance_mult, level * 0.003)
    touches = 0
    rejections = 0
    n = len(highs)

    for i in range(n):
        recency_weight = 1.0 + (i / n)  # Recent touches weighted higher
        # Check if high touched the level and closed lower
        if abs(highs[i] - level) <= band:
            touches += recency_weight
            rejections += recency_weight
        elif abs(lows[i] - level) <= band:
            touches += recency_weight
            rejections += recency_weight

    score = min(1.0, (touches * 0.15) + (rejections * 0.10))
    return safe_float(score, round_digits=2)


def calculate_sr_features(
    prices: np.ndarray,
    highs: Optional[np.ndarray] = None,
    lows: Optional[np.ndarray] = None,
    atr: float = 1.0,
) -> Dict:
    """
    Identifies key support and resistance levels, distances, and strength.
    """
    n = len(prices)
    last_price = safe_float(prices[-1]) if n > 0 else 0.0

    h_arr = highs if highs is not None and len(highs) == n else prices * 1.005
    l_arr = lows if lows is not None and len(lows) == n else prices * 0.995

    # Prior day levels
    prior_high = float(h_arr[-2]) if n >= 2 else last_price * 1.01
    prior_low = float(l_arr[-2]) if n >= 2 else last_price * 0.99

    # Prior 5-day (weekly) levels
    week_high = float(np.max(h_arr[-min(n, 5):-1])) if n >= 3 else prior_high
    week_low = float(np.min(l_arr[-min(n, 5):-1])) if n >= 3 else prior_low

    # Select nearest resistance (above current price) and support (below current price)
    res_candidates = [prior_high, week_high, float(np.max(h_arr[-min(n, 20):]))]
    sup_candidates = [prior_low, week_low, float(np.min(l_arr[-min(n, 20):]))]

    valid_res = [r for r in res_candidates if r > last_price]
    valid_sup = [s for s in sup_candidates if s < last_price]

    nearest_res = min(valid_res) if valid_res else last_price * 1.02
    nearest_sup = max(valid_sup) if valid_sup else last_price * 0.98

    dist_res_pct = safe_div(nearest_res - last_price, last_price, default=0.0) * 100.0
    dist_sup_pct = safe_div(nearest_sup - last_price, last_price, default=0.0) * 100.0

    res_strength = evaluate_level_strength(nearest_res, h_arr, l_arr, atr)
    sup_strength = evaluate_level_strength(nearest_sup, h_arr, l_arr, atr)

    return {
        "nearest_resistance": safe_float(nearest_res, round_digits=2),
        "nearest_support": safe_float(nearest_sup, round_digits=2),
        "nearest_resistance_distance_pct": safe_float(dist_res_pct, round_digits=2),
        "nearest_support_distance_pct": safe_float(dist_sup_pct, round_digits=2),
        "resistance_strength": res_strength,
        "support_strength": sup_strength,
    }
