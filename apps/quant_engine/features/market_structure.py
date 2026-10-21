"""
Market Structure & Swing Analysis Module.

Detects swing highs/lows (Higher Highs, Higher Lows, Lower Highs, Lower Lows)
and statistically confirmed breakouts/breakdowns using ATR threshold multiples.
"""
from typing import Dict, List, Literal, Optional, Tuple
import numpy as np
from .data_quality import safe_float, safe_div


def find_swing_points(
    highs: np.ndarray,
    lows: np.ndarray,
    pivot_window: int = 3,
) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """
    Identifies local swing highs and swing lows across the time series.
    Returns (swing_highs, swing_lows) as lists of (index, price).
    """
    n = len(highs)
    swing_highs = []
    swing_lows = []
    
    if n < pivot_window * 2 + 1:
        return swing_highs, swing_lows

    for i in range(pivot_window, n - pivot_window):
        # Swing High
        if highs[i] == np.max(highs[i - pivot_window:i + pivot_window + 1]):
            swing_highs.append((i, float(highs[i])))
        # Swing Low
        if lows[i] == np.min(lows[i - pivot_window:i + pivot_window + 1]):
            swing_lows.append((i, float(lows[i])))

    return swing_highs, swing_lows


def classify_swing_structure(
    swing_highs: List[Tuple[int, float]],
    swing_lows: List[Tuple[int, float]],
) -> Literal["higher_highs_higher_lows", "lower_highs_lower_lows", "range", "transition"]:
    """Classifies the sequence of swing highs and lows into structural regime."""
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "range"

    last_sh = swing_highs[-1][1]
    prev_sh = swing_highs[-2][1]
    last_sl = swing_lows[-1][1]
    prev_sl = swing_lows[-2][1]

    hh = last_sh > prev_sh
    hl = last_sl > prev_sl
    lh = last_sh < prev_sh
    ll = last_sl < prev_sl

    if hh and hl:
        return "higher_highs_higher_lows"
    elif lh and ll:
        return "lower_highs_lower_lows"
    elif hh and ll:
        return "transition"  # Expanding volatility / broadening
    else:
        return "range"


def calculate_market_structure_features(
    prices: np.ndarray,
    highs: Optional[np.ndarray] = None,
    lows: Optional[np.ndarray] = None,
    atr: float = 1.0,
    pivot_window: int = 3,
) -> Dict:
    """
    Computes swing structure classification, breakout/breakdown detection, and structural state.
    """
    n = len(prices)
    last_price = safe_float(prices[-1]) if n > 0 else 0.0

    h_arr = highs if highs is not None and len(highs) == n else prices * 1.005
    l_arr = lows if lows is not None and len(lows) == n else prices * 0.995

    swing_highs, swing_lows = find_swing_points(h_arr, l_arr, pivot_window=pivot_window)
    swing_struct = classify_swing_structure(swing_highs, swing_lows)

    # Reference structural levels
    nearest_res = swing_highs[-1][1] if swing_highs else float(np.max(h_arr[-min(n, 20):]))
    nearest_sup = swing_lows[-1][1] if swing_lows else float(np.min(l_arr[-min(n, 20):]))

    # Confirm breakout using ATR multiple
    breakout_confirmed = False
    state: Literal["bullish_breakout", "bearish_breakdown", "range_bound", "testing_resistance", "testing_support", "normal"] = "normal"

    if last_price > nearest_res:
        if (last_price - nearest_res) >= (0.3 * atr):
            breakout_confirmed = True
            state = "bullish_breakout"
        else:
            state = "testing_resistance"
    elif last_price < nearest_sup:
        if (nearest_sup - last_price) >= (0.3 * atr):
            breakout_confirmed = True
            state = "bearish_breakdown"
        else:
            state = "testing_support"
    else:
        dist_res_pct = abs(nearest_res - last_price) / max(last_price, 0.001) * 100.0
        dist_sup_pct = abs(last_price - nearest_sup) / max(last_price, 0.001) * 100.0
        if dist_res_pct < 0.6:
            state = "testing_resistance"
        elif dist_sup_pct < 0.6:
            state = "testing_support"
        else:
            state = "range_bound" if swing_struct == "range" else "normal"

    return {
        "state": state,
        "swing_structure": swing_struct,
        "breakout_confirmed": breakout_confirmed,
        "nearest_resistance": safe_float(nearest_res, round_digits=2),
        "nearest_support": safe_float(nearest_sup, round_digits=2),
    }
