"""
Event & Report Quantification Module.

Quantifies economic and catalyst release surprises (Actual - Forecast)
and immediate multi-horizon market price and volatility reactions.
"""
from typing import Dict, Optional
from .data_quality import safe_float, safe_div


def calculate_event_features(
    event_name: Optional[str] = None,
    actual: Optional[float] = None,
    forecast: Optional[float] = None,
    historical_std: Optional[float] = None,
    price_before: Optional[float] = None,
    price_after_1h: Optional[float] = None,
    vol_reaction_pct: Optional[float] = None,
) -> Dict:
    """
    Computes report surprise, standardized surprise, and immediate market reaction metrics.
    """
    if actual is None or forecast is None:
        return {
            "latest_event": event_name,
            "surprise": None,
            "standardized_surprise": None,
            "immediate_reaction_1h_pct": None,
            "reaction_volatility_pct": None,
        }

    surprise = actual - forecast
    std_denom = historical_std if (historical_std is not None and historical_std > 0) else max(abs(forecast) * 0.1, 1.0)
    std_surprise = safe_div(surprise, std_denom, default=0.0)

    # Price reaction 1h
    if price_before is not None and price_after_1h is not None and price_before > 0:
        reaction_1h = (price_after_1h - price_before) / price_before * 100.0
    else:
        reaction_1h = None

    return {
        "latest_event": event_name,
        "surprise": safe_float(surprise, round_digits=2),
        "standardized_surprise": safe_float(std_surprise, round_digits=2),
        "immediate_reaction_1h_pct": safe_float(reaction_1h, round_digits=2) if reaction_1h is not None else None,
        "reaction_volatility_pct": safe_float(vol_reaction_pct, round_digits=2) if vol_reaction_pct is not None else None,
    }
