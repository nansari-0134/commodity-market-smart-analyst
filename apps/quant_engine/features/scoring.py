"""
Quantitative Scoring & Composite State Module.

Calculates standardized quantitative scores normalized to [-1.0, +1.0]
and [0.0, 1.0] across all 10 analytical dimensions with transparent mathematical logic.
"""
from typing import Dict
import numpy as np
from .data_quality import safe_float


def compute_quantitative_scores(
    trend_dict: Dict,
    momentum_dict: Dict,
    volatility_dict: Dict,
    volume_dict: Dict,
    structure_dict: Dict,
    curve_dict: Dict,
    relative_value_dict: Dict,
    fundamentals_dict: Dict,
    events_dict: Dict,
) -> Dict[str, float]:
    """
    Computes transparent, continuous normalized scores across each core dimension.
    """
    # 1. Trend Score [-1.0, +1.0]
    ema_s = trend_dict.get("ema_structure", "neutral")
    base_t = 0.5 if ema_s == "bullish" else (-0.5 if ema_s == "bearish" else 0.0)
    adx_mult = min(1.0, trend_dict.get("adx", 20.0) / 40.0)
    dist_20 = np.clip(trend_dict.get("dist_ema20_pct", 0.0) / 3.0, -1.0, 1.0)
    trend_score = np.clip((base_t * 0.6) + (base_t * adx_mult * 0.2) + (dist_20 * 0.2), -1.0, 1.0)

    # 2. Momentum Score [-1.0, +1.0]
    rsi = momentum_dict.get("rsi", 50.0)
    rsi_norm = np.clip((rsi - 50.0) / 25.0, -1.0, 1.0)
    hist_dir = momentum_dict.get("histogram_direction", "flat")
    hist_bonus = 0.2 if hist_dir == "increasing" else (-0.2 if hist_dir == "decreasing" else 0.0)
    momentum_score = np.clip((rsi_norm * 0.8) + hist_bonus, -1.0, 1.0)

    # 3. Volatility Score [0.0, 1.0] (Measures volatility expansion)
    vol_pct = volatility_dict.get("vol_percentile", 50.0) / 100.0
    volatility_score = np.clip(vol_pct, 0.0, 1.0)

    # 4. Volume Score [0.0, 1.0] (Measures institutional participation)
    rvol = volume_dict.get("relative_volume", 1.0)
    volume_score = np.clip(rvol / 2.0, 0.0, 1.0)

    # 5. Market Structure Score [-1.0, +1.0]
    sw_struct = structure_dict.get("swing_structure", "range")
    base_sw = 0.5 if sw_struct == "higher_highs_higher_lows" else (-0.5 if sw_struct == "lower_highs_lower_lows" else 0.0)
    r_pos = (structure_dict.get("range_position_20d", 50.0) - 50.0) / 50.0
    st_state = structure_dict.get("state", "normal")
    bo_bonus = 0.25 if st_state == "bullish_breakout" else (-0.25 if st_state == "bearish_breakdown" else 0.0)
    structure_score = np.clip((base_sw * 0.4) + (r_pos * 0.35) + bo_bonus, -1.0, 1.0)

    # 6. Futures Curve Score [-1.0, +1.0] (Backwardation = Bullish, Contango = Bearish)
    c_state = curve_dict.get("curve_state", "flat")
    if "backwardation" in c_state:
        base_c = 0.8 if "strong" in c_state else 0.4
    elif "contango" in c_state:
        base_c = -0.8 if "strong" in c_state else -0.4
    else:
        base_c = 0.0
    c_z = np.clip(curve_dict.get("spread_zscore", 0.0) / 2.0, -0.5, 0.5)
    curve_score = np.clip((base_c * 0.7) + (c_z * 0.3), -1.0, 1.0)

    # 7. Relative Value Score [-1.0, +1.0] (Mean reversion: rich is negative, cheap is positive)
    rv_z = relative_value_dict.get("spread_zscore", 0.0)
    relative_value_score = np.clip(-rv_z / 2.0, -1.0, 1.0)

    # 8. Fundamentals Score [-1.0, +1.0] (Tightening / Deficit is Bullish +1.0)
    inv_z = fundamentals_dict.get("inventory_zscore")
    if inv_z is not None:
        fundamentals_score = np.clip(-inv_z / 2.0, -1.0, 1.0)
    else:
        f_mom = fundamentals_dict.get("fundamental_momentum", "neutral")
        fundamentals_score = 0.5 if f_mom in ["tightening", "drawing"] else (-0.5 if f_mom in ["loosening", "building"] else 0.0)

    # 9. Event Score [-1.0, +1.0]
    ev_std = events_dict.get("standardized_surprise")
    event_score = np.clip(ev_std / 2.0, -1.0, 1.0) if ev_std is not None else 0.0

    # 10. Overall Composite Score [-1.0, +1.0]
    # Multi-factor weights: Trend (25%), Momentum (20%), Structure (20%), Curve (15%), Fundamentals (10%), RV (10%)
    overall = (
        (trend_score * 0.25)
        + (momentum_score * 0.20)
        + (structure_score * 0.20)
        + (curve_score * 0.15)
        + (fundamentals_score * 0.10)
        + (relative_value_score * 0.10)
    )

    return {
        "trend_score": safe_float(trend_score, round_digits=2),
        "momentum_score": safe_float(momentum_score, round_digits=2),
        "volatility_score": safe_float(volatility_score, round_digits=2),
        "volume_score": safe_float(volume_score, round_digits=2),
        "structure_score": safe_float(structure_score, round_digits=2),
        "curve_score": safe_float(curve_score, round_digits=2),
        "relative_value_score": safe_float(relative_value_score, round_digits=2),
        "fundamentals_score": safe_float(fundamentals_score, round_digits=2),
        "event_score": safe_float(event_score, round_digits=2),
        "overall_composite_score": safe_float(overall, round_digits=2),
    }
