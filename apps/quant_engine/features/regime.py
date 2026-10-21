"""
Market Regime Detection Module.

Combines trend direction & strength with volatility expansion states
into an unambiguous rule-based market regime classification.
"""
from typing import Dict


def determine_market_regime(
    trend_state: str,
    volatility_regime: str,
    momentum_state: str = "neutral",
) -> Dict[str, str]:
    """
    Synthesizes multi-factor regime: trend × volatility.
    
    Examples:
      - strong_bullish × high -> 'bullish_high_volatility'
      - ranging × low -> 'range_low_volatility'
      - strong_bearish × extreme -> 'bearish_extreme_volatility'
    """
    clean_trend = trend_state.replace("strong_", "").replace("weak_", "")
    overall = f"{clean_trend}_{volatility_regime}_volatility"
    
    if trend_state == "ranging":
        overall = f"range_{volatility_regime}_volatility"

    return {
        "trend": trend_state,
        "volatility": volatility_regime,
        "overall": overall,
    }
