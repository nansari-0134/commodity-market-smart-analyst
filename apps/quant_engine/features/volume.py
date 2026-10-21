"""
Volume Analysis Module.

Calculates Relative Volume (RVOL), rolling Volume Z-score,
and institutional participation regimes.
"""
from typing import Dict, Literal
import numpy as np
from .data_quality import safe_float, safe_div


def calculate_volume_features(
    volumes: np.ndarray,
    rvol_window: int = 20,
) -> Dict:
    """
    Computes volume metrics: latest volume, RVOL, volume Z-score, and participation state.
    """
    if len(volumes) == 0:
        return {
            "volume": 0,
            "relative_volume": 1.0,
            "zscore": 0.0,
            "state": "normal",
        }

    latest_vol = int(volumes[-1])
    window = volumes[-min(len(volumes), rvol_window):]

    if len(window) >= 2:
        mean_vol = float(np.mean(window[:-1])) if len(window) > 1 else float(window[0])
        std_vol = float(np.std(window[:-1], ddof=1)) if len(window) > 2 else (mean_vol * 0.3)
        
        rvol = safe_div(float(latest_vol), mean_vol, default=1.0) if mean_vol > 0 else 1.0
        zscore = safe_div(float(latest_vol) - mean_vol, std_vol, default=0.0) if std_vol > 0 else 0.0
    else:
        rvol = 1.0
        zscore = 0.0

    # Volume State
    if rvol >= 2.0 or zscore >= 2.0:
        state: Literal["unusually_low", "low", "normal", "high", "unusually_high"] = "unusually_high"
    elif rvol >= 1.25 or zscore >= 1.0:
        state = "high"
    elif rvol <= 0.5 or zscore <= -1.5:
        state = "unusually_low"
    elif rvol <= 0.75:
        state = "low"
    else:
        state = "normal"

    return {
        "volume": latest_vol,
        "relative_volume": safe_float(rvol, round_digits=2),
        "zscore": safe_float(zscore, round_digits=2),
        "state": state,
    }
