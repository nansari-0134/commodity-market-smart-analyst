"""
Forward Curve & Term Structure Analytics Core.

Calculates deterministic curve structure metrics:
- Prompt 1M vs 2M calendar spread
- Annualized Roll Yield: (M1 - M12) / M1
- Slope regime: Contango vs Backwardation intensity
- Butterfly curvature: 2*M2 - (M1 + M3)
"""
from typing import Literal


def analyze_curve_structure(
    m1_price: float,
    m2_price: float,
    m3_price: float | None = None,
    m12_price: float | None = None,
) -> dict:
    """
    Analyze term structure slope, spreads, and curvature from forward contract prices.
    
    Args:
        m1_price: Prompt front-month contract price.
        m2_price: Second month forward contract price.
        m3_price: Third month forward contract price (optional).
        m12_price: 1-year forward contract price (optional, defaults to extrapolation).
        
    Returns:
        Dictionary containing prompt_spread, roll_yield_1y, curve_state, and butterfly.
    """
    if m1_price <= 0:
        return {
            "prompt_spread": 0.0,
            "roll_yield_1y": 0.0,
            "curve_state": "FLAT",
            "butterfly": 0.0,
        }
        
    prompt_spread = round(float(m1_price - m2_price), 4)
    
    # 1Y roll yield: (M1 - M12) / M1 * 100%
    if m12_price and m12_price > 0:
        roll_yield_1y = round(float((m1_price - m12_price) / m1_price * 100), 2)
    else:
        # Approximate 1Y roll yield from 1M-2M prompt slope: prompt_spread / m1 * 12 * 100%
        roll_yield_1y = round(float((prompt_spread / m1_price) * 12 * 100), 2)
        
    # Butterfly curvature: 2*M2 - (M1 + M3)
    if m3_price and m3_price > 0:
        butterfly = round(float(2 * m2_price - (m1_price + m3_price)), 4)
    else:
        butterfly = 0.0
        
    # Curve classification
    # Backwardation: prompt > forward (positive roll yield)
    # Contango: prompt < forward (negative roll yield)
    if roll_yield_1y >= 6.0 or prompt_spread > 0.02 * m1_price:
        curve_state = "STRONG_BACKWARDATION"
    elif roll_yield_1y >= 1.0 or prompt_spread > 0.005 * m1_price:
        curve_state = "MILD_BACKWARDATION"
    elif roll_yield_1y <= -6.0 or prompt_spread < -0.02 * m1_price:
        curve_state = "STRONG_CONTANGO"
    elif roll_yield_1y <= -1.0 or prompt_spread < -0.005 * m1_price:
        curve_state = "MILD_CONTANGO"
    else:
        curve_state = "FLAT"
        
    return {
        "prompt_spread": prompt_spread,
        "roll_yield_1y": roll_yield_1y,
        "curve_state": curve_state,
        "butterfly": butterfly,
    }
