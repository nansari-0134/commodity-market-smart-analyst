"""
Order Flow & Microstructure Module.

Processes tick-level aggressive buy/sell imbalances and cumulative delta.
Adheres strictly to Rule: Mark fields as UNAVAILABLE if high-frequency tick/L2 data
is absent; never fabricate order book flow from daily OHLC bars.
"""
from typing import Dict, Literal, Optional
from .data_quality import safe_float


def calculate_order_flow_features(
    buy_volume: Optional[float] = None,
    sell_volume: Optional[float] = None,
    cumulative_delta: Optional[float] = None,
) -> Dict:
    """
    Computes order flow imbalance and delta regime when tick-level volume is available.
    """
    if buy_volume is None or sell_volume is None:
        return {
            "imbalance": None,
            "cumulative_delta": None,
            "delta_direction": "unavailable",
            "is_available": False,
        }

    total_vol = buy_volume + sell_volume
    if total_vol <= 0:
        return {
            "imbalance": 0.0,
            "cumulative_delta": safe_float(cumulative_delta, default=0.0),
            "delta_direction": "neutral",
            "is_available": True,
        }

    imbalance = (buy_volume - sell_volume) / total_vol

    if imbalance > 0.20:
        direction: Literal["aggressive_buying", "aggressive_selling", "neutral", "unavailable"] = "aggressive_buying"
    elif imbalance < -0.20:
        direction = "aggressive_selling"
    else:
        direction = "neutral"

    return {
        "imbalance": safe_float(imbalance, round_digits=3),
        "cumulative_delta": safe_float(cumulative_delta, default=0.0),
        "delta_direction": direction,
        "is_available": True,
    }
