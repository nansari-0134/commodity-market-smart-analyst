"""
Liquidity & Market Depth Module.

Measures top-of-book bid-ask spread and L2 depth imbalance.
Adheres strictly to the requirement: Never fabricate depth features from OHLC.
"""
from typing import Dict, Optional
import numpy as np
from .data_quality import safe_float, safe_div


def calculate_liquidity_features(
    bid: Optional[float] = None,
    ask: Optional[float] = None,
    tick_size: float = 0.01,
    bid_depth: Optional[float] = None,
    ask_depth: Optional[float] = None,
    historical_spreads: Optional[np.ndarray] = None,
) -> Dict:
    """
    Computes top-of-book spread and depth imbalance when live book quotes exist.
    """
    if bid is None or ask is None or ask <= bid:
        return {
            "bid_ask_spread": None,
            "bid_ask_spread_ticks": None,
            "spread_percentile": None,
            "depth_imbalance": None,
            "is_available": False,
        }

    spread_abs = ask - bid
    spread_ticks = safe_div(spread_abs, tick_size, default=1.0)

    # Spread percentile vs history
    if historical_spreads is not None and len(historical_spreads) >= 5:
        pct = float(np.mean(historical_spreads <= spread_abs) * 100.0)
    else:
        pct = 50.0

    # Depth imbalance
    depth_imb = None
    if bid_depth is not None and ask_depth is not None and (bid_depth + ask_depth) > 0:
        depth_imb = safe_div(bid_depth - ask_depth, bid_depth + ask_depth, default=0.0)

    return {
        "bid_ask_spread": safe_float(spread_abs, round_digits=4),
        "bid_ask_spread_ticks": safe_float(spread_ticks, round_digits=1),
        "spread_percentile": safe_float(pct, round_digits=1),
        "depth_imbalance": safe_float(depth_imb, round_digits=3) if depth_imb is not None else None,
        "is_available": True,
    }
