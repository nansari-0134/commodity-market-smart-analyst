"""
Base Provider Contract and DTOs for Commodity Reference Data.
Follows the Universal Provider Architecture (docs/guides/data-sources.md).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List, Dict, Any


@dataclass
class RawExchangeListingSpec:
    """Normalized DTO for an exchange listing of a commodity."""
    exchange_code: str
    ticker_symbol: str
    contract_size: Decimal
    contract_unit_code: str
    settlement_method: str = "PHYSICAL"
    is_primary_benchmark: bool = False
    liquidity_tier: str = "ACTIVE"
    typical_daily_volume: int = 0
    typical_open_interest: int = 0
    trading_currency: str = "USD"
    is_active: bool = True


@dataclass
class RawCommoditySpec:
    """Normalized DTO for a canonical physical commodity specification."""
    code: str
    name: str
    sector: str
    group: str
    primary_exchange_code: str
    base_unit_code: str
    pricing_unit_code: str
    standard_lot_size: Decimal
    standard_lot_unit_code: str
    minimum_tick_size: Decimal
    tick_value: Decimal
    tick_currency: str = "USD"
    settlement_method: str = "PHYSICAL"
    hs_code: str = ""
    deliverable_grade_standard: str = ""
    quality_specifications: Dict[str, Any] = field(default_factory=dict)
    primary_delivery_hub: str = ""
    delivery_hub_details: Dict[str, Any] = field(default_factory=dict)
    crop_year_start_month: Optional[int] = None
    peak_production_months: List[int] = field(default_factory=list)
    peak_demand_months: List[int] = field(default_factory=list)
    seasonality_notes: str = ""
    description: str = ""
    display_order: int = 0
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    listings: List[RawExchangeListingSpec] = field(default_factory=list)


class BaseCommodityCatalogProvider(ABC):
    """
    Abstract interface contract for commodity catalog providers.
    All external vendors (e.g. CME Datamine, Refinitiv, Argus, Static Catalog)
    must implement this contract.
    """

    @abstractmethod
    def get_commodities(self) -> List[RawCommoditySpec]:
        """Fetch all canonical commodity specifications."""
        raise NotImplementedError

    @abstractmethod
    def get_commodity(self, code: str) -> Optional[RawCommoditySpec]:
        """Fetch a specific commodity by canonical code."""
        raise NotImplementedError
