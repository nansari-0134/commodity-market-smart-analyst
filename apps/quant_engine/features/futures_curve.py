"""
Futures Curve & Term Structure Analysis Module.

Calculates prompt calendar spreads (F1-F2, F2-F3, F1-F3), spread Z-scores,
percentiles, annualized slopes, and contango/backwardation curve regimes.
"""
from typing import Dict, List, Literal, Optional
import numpy as np
from .data_quality import safe_float, safe_div


def classify_curve_state(
    spread_f1_f2: float,
    f1_price: float,
    annualized_slope: float,
) -> Literal["strong_backwardation", "backwardation", "flat", "contango", "strong_contango"]:
    """
    Classifies the term structure state of the futures curve.
    In commodity futures:
      F1 > F2 -> Backwardation (positive roll yield, convenience yield > carry cost)
      F1 < F2 -> Contango (negative roll yield, carry cost > convenience yield)
    """
    if f1_price <= 0:
        return "flat"

    pct_diff = (spread_f1_f2 / f1_price) * 100.0
    if pct_diff > 1.5 or annualized_slope < -0.10:
        return "strong_backwardation"
    elif pct_diff > 0.2:
        return "backwardation"
    elif pct_diff < -1.5 or annualized_slope > 0.10:
        return "strong_contango"
    elif pct_diff < -0.2:
        return "contango"
    else:
        return "flat"


def calculate_curve_features(
    contract_prices: List[float],
    historical_spreads: Optional[np.ndarray] = None,
) -> Dict:
    """
    Computes calendar spreads, Z-scores, percentiles, slope, and curve state.
    
    Args:
        contract_prices: List of consecutive settlement prices [F1, F2, F3, ..., F12].
        historical_spreads: Optional 1D array of historical F1-F2 spreads for Z-score/percentile.
    """
    if not contract_prices or len(contract_prices) < 2:
        return {
            "spread_f1_f2": 0.0,
            "spread_f2_f3": 0.0,
            "spread_f1_f3": 0.0,
            "spread_zscore": 0.0,
            "spread_percentile": 50.0,
            "curve_state": "flat",
            "curve_slope_annualized": 0.0,
        }

    f1 = float(contract_prices[0])
    f2 = float(contract_prices[1])
    f3 = float(contract_prices[2]) if len(contract_prices) >= 3 else f2
    f_far = float(contract_prices[-1])

    # Calendar spreads: F_near - F_deferred
    spread_f1_f2 = f1 - f2
    spread_f2_f3 = f2 - f3
    spread_f1_f3 = f1 - f3

    # Term structure slope annualized
    num_months = max(1, len(contract_prices) - 1)
    annualized_slope = safe_div(f_far - f1, f1 * (num_months / 12.0), default=0.0)

    # Historical Z-score and percentile
    if historical_spreads is not None and len(historical_spreads) >= 5:
        mean_s = float(np.mean(historical_spreads))
        std_s = float(np.std(historical_spreads, ddof=1)) if len(historical_spreads) > 1 else 0.1
        zscore = safe_div(spread_f1_f2 - mean_s, std_s, default=0.0)
        pct = float(np.mean(historical_spreads <= spread_f1_f2) * 100.0)
    else:
        # Default estimation based on spread percentage
        pct_spread = safe_div(spread_f1_f2, f1, default=0.0) * 100.0
        zscore = np.clip(pct_spread * 1.5, -3.0, 3.0)
        pct = np.clip(50.0 + (zscore * 18.0), 0.0, 100.0)

    curve_state = classify_curve_state(spread_f1_f2, f1, annualized_slope)

    return {
        "spread_f1_f2": safe_float(spread_f1_f2, round_digits=3),
        "spread_f2_f3": safe_float(spread_f2_f3, round_digits=3),
        "spread_f1_f3": safe_float(spread_f1_f3, round_digits=3),
        "spread_zscore": safe_float(zscore, round_digits=2),
        "spread_percentile": safe_float(pct, round_digits=1),
        "curve_state": curve_state,
        "curve_slope_annualized": safe_float(annualized_slope, round_digits=4),
    }
