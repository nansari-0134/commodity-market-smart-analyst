"""
Base Contract Specification Provider Interface and Data Transfer Objects (DTOs).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date as dt_date
from decimal import Decimal
from typing import List, Optional


@dataclass(frozen=True)
class RawContractExpiryDTO:
    """Strongly-typed DTO representing a single delivery contract expiry."""

    contract_symbol: str
    contract_year: int
    contract_month: int
    contract_month_code: str
    last_trading_day: dt_date
    first_notice_day: Optional[dt_date]
    last_delivery_day: Optional[dt_date]
    final_settlement_date: dt_date
    is_expired: bool = False


@dataclass(frozen=True)
class RawContractSpec:
    """Strongly-typed DTO representing an institutional contract specification."""

    commodity_code: str
    exchange_mic: str
    symbol_root: str
    name: str
    contract_size: Decimal
    contract_unit_code: str
    price_quote_unit_code: str
    minimum_tick_size: Decimal
    tick_value: Decimal
    trading_currency: str = "USD"
    instrument_type: str = "FUTURES"
    settlement_method: str = "PHYSICAL"
    trading_months: str = "ALL_12"
    expiry_rule: str = "DAY_OF_PRIOR_MONTH_WITH_BUS_OFFSET"
    expiry_rule_parameter: int = 25
    notice_rule: str = "First business day prior to first delivery day"
    default_roll_rule: str = "GSCI_5_TO_9_BUS_DAY"
    prompt_cycles_to_seed: int = 12
    display_order: int = 100


class BaseContractSpecProvider(ABC):
    """
    Abstract interface for contract specification and delivery schedule feeds.
    Enforces isolation of vendor protocols (CME Datamine, ICE Data Services, Bloomberg, Refinitiv)
    from downstream quantitative models.
    """

    @abstractmethod
    def get_specifications(self) -> List[RawContractSpec]:
        """Fetch all canonical contract specifications."""
        pass

    @abstractmethod
    def get_specification(self, symbol_root: str, exchange_mic: str) -> Optional[RawContractSpec]:
        """Retrieve a single specification by ticker root and venue MIC."""
        pass
