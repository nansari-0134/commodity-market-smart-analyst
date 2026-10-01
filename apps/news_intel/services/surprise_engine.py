"""
Macroeconomic Catalyst Surprise Calculation Engine.
Evaluates scheduled vs actual economic/inventory data releases,
computes consensus deltas, and assigns deterministic market surprise directions.
"""

from decimal import Decimal
from typing import Optional, Tuple
from apps.news_intel.models import EventType, SurpriseDirection


class CatalystSurpriseEngine:
    """
    Deterministic engine evaluating market catalyst surprise deltas and economic directional impact.
    """

    @classmethod
    def evaluate_surprise(
        cls,
        actual_value: Optional[Decimal],
        consensus_expectation: Optional[Decimal],
        event_type: str,
        event_name: str = "",
    ) -> Tuple[Optional[Decimal], str]:
        """
        Compute surprise magnitude and economic direction based on institutional market mechanics.
        """
        if actual_value is None or consensus_expectation is None:
            return None, SurpriseDirection.UNAVAILABLE

        delta = (actual_value - consensus_expectation).quantize(Decimal("0.0001"))

        # Tolerance threshold for "in-line"
        tolerance = Decimal("0.0001")
        if abs(delta) <= tolerance:
            return delta, SurpriseDirection.IN_LINE

        name_lower = event_name.lower()

        # 1. Inventory Reports (EIA Crude, Products, Natural Gas Storage)
        if event_type == EventType.INVENTORY_EIA or "inventor" in name_lower or "storage" in name_lower:
            # For inventory changes/levels:
            # An actual number less than consensus (e.g. larger draw or smaller build) is BULLISH.
            # An actual number greater than consensus (e.g. smaller draw or larger build) is BEARISH.
            if delta < Decimal("0.0000"):
                return delta, SurpriseDirection.BULLISH_SURPRISE
            else:
                return delta, SurpriseDirection.BEARISH_SURPRISE

        # 2. Agricultural Crop Supply Reports (WASDE Yields & Ending Stocks)
        elif event_type == EventType.GOVERNMENT_WASDE or "wasde" in name_lower or "crop progress" in name_lower:
            # Lower crop yields or tighter ending stocks than consensus = BULLISH
            if delta < Decimal("0.0000"):
                return delta, SurpriseDirection.BULLISH_SURPRISE
            else:
                return delta, SurpriseDirection.BEARISH_SURPRISE

        # 3. Central Bank Policy (Interest Rates)
        elif event_type == EventType.MACRO_CENTRAL_BANK or "rate" in name_lower or "fomc" in name_lower:
            # Lower policy rates reduce borrowing costs and weigh on fiat currency = BULLISH for commodities/gold
            if delta < Decimal("0.0000"):
                return delta, SurpriseDirection.BULLISH_SURPRISE
            else:
                return delta, SurpriseDirection.BEARISH_SURPRISE

        # 4. OPEC Production Quotas
        elif event_type == EventType.POLICY_OPEC or "opec" in name_lower:
            # Deeper production cuts = BULLISH
            if delta < Decimal("0.0000"):
                return delta, SurpriseDirection.BULLISH_SURPRISE
            else:
                return delta, SurpriseDirection.BEARISH_SURPRISE

        # Default economic indicator logic (e.g. GDP, manufacturing PMI, consumer demand):
        # Higher than consensus = BULLISH for demand
        if delta > Decimal("0.0000"):
            return delta, SurpriseDirection.BULLISH_SURPRISE
        else:
            return delta, SurpriseDirection.BEARISH_SURPRISE
