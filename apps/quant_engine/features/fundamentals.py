"""
Fundamental Quantification Module.

Quantifies physical inventory/balance deviations against 5-year seasonal normals
and tracks fundamental momentum (tightening, loosening, building, drawing).
"""
from typing import Dict, Literal, Optional
import numpy as np
from .data_quality import safe_float, safe_div


def calculate_fundamental_features(
    variable_name: Optional[str] = None,
    current_value: Optional[float] = None,
    reference_normal: Optional[float] = None,
    prior_value: Optional[float] = None,
    historical_observations: Optional[np.ndarray] = None,
) -> Dict:
    """
    Computes fundamental deviations, Z-score, and momentum.
    """
    if current_value is None or reference_normal is None:
        return {
            "primary_variable": variable_name,
            "latest_value": None,
            "normal_reference": None,
            "deviation_abs": None,
            "deviation_pct": None,
            "inventory_zscore": None,
            "fundamental_momentum": "unavailable",
        }

    dev_abs = current_value - reference_normal
    dev_pct = safe_div(dev_abs, reference_normal, default=0.0) * 100.0

    # Z-score vs historical distribution
    if historical_observations is not None and len(historical_observations) >= 5:
        std_val = float(np.std(historical_observations, ddof=1)) if len(historical_observations) > 1 else 1.0
        zscore = safe_div(dev_abs, std_val, default=0.0)
    else:
        zscore = np.clip(dev_pct / 10.0, -3.5, 3.5)

    # Fundamental momentum
    if prior_value is not None:
        delta = current_value - prior_value
        if delta < 0:
            # Draw / tightening
            momentum: Literal["tightening", "loosening", "building", "drawing", "neutral", "unavailable"] = "drawing" if "STOCK" in (variable_name or "").upper() else "tightening"
        elif delta > 0:
            # Build / loosening
            momentum = "building" if "STOCK" in (variable_name or "").upper() else "loosening"
        else:
            momentum = "neutral"
    else:
        if dev_pct < -5.0:
            momentum = "tightening"
        elif dev_pct > 5.0:
            momentum = "loosening"
        else:
            momentum = "neutral"

    return {
        "primary_variable": variable_name,
        "latest_value": safe_float(current_value, round_digits=2),
        "normal_reference": safe_float(reference_normal, round_digits=2),
        "deviation_abs": safe_float(dev_abs, round_digits=2),
        "deviation_pct": safe_float(dev_pct, round_digits=2),
        "inventory_zscore": safe_float(zscore, round_digits=2),
        "fundamental_momentum": momentum,
    }
