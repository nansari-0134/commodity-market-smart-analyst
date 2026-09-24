"""
Abstract Provider Interfaces and Data Transfer Objects (DTOs).

Provides the Strategy contract for:
1. BaseMarketDataProvider: Ingests exchange settlements, OHLCV, volume, and open interest.
2. BaseFundamentalProvider: Ingests balances, stocks, storage, production, and trade flows.
3. BaseCOTProvider: Ingests CFTC Commitment of Traders positioning.

All providers return normalized, lightweight Python dataclasses, decoupling the ingestion
pipeline from external vendor schemas, formats (JSON/XML/CSV), and authentication protocols.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class RawPriceObservation:
    """Normalized DTO for price bar observations returned by market data providers."""
    symbol: str
    observation_date: date
    contract_month: str = ""
    is_prompt: bool = True
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    settlement_price: Optional[Decimal] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    publication_time: Optional[datetime] = None
    is_preliminary: bool = False
    source_endpoint_code: Optional[str] = None


@dataclass(frozen=True)
class RawFundamentalObservation:
    """Normalized DTO for fundamental balance/inventory metrics."""
    variable_code: str
    observation_date: date
    value: Optional[Decimal] = None
    unit_code: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    publication_time: Optional[datetime] = None
    is_preliminary: bool = False
    revision_number: int = 0
    source_endpoint_code: Optional[str] = None


@dataclass(frozen=True)
class RawCOTObservation:
    """Normalized DTO for CFTC Commitment of Traders positioning."""
    commodity_code: str
    observation_date: date
    report_type: str = "DISAGGREGATED"
    open_interest: int = 0
    prod_merc_long: Optional[int] = None
    prod_merc_short: Optional[int] = None
    swap_long: Optional[int] = None
    swap_short: Optional[int] = None
    swap_spread: Optional[int] = None
    money_manager_long: Optional[int] = None
    money_manager_short: Optional[int] = None
    money_manager_spread: Optional[int] = None
    other_rept_long: Optional[int] = None
    other_rept_short: Optional[int] = None
    non_rept_long: Optional[int] = None
    non_rept_short: Optional[int] = None
    publication_time: Optional[datetime] = None
    source_endpoint_code: Optional[str] = None


class BaseMarketDataProvider(ABC):
    """Abstract interface for all market pricing adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Vendor or feed human-readable name."""
        pass

    @abstractmethod
    def fetch_price_observations(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs,
    ) -> list[RawPriceObservation]:
        """Fetch historical or daily price observations for a given commodity symbol."""
        pass

    def is_healthy(self) -> bool:
        """Check provider connectivity and health status."""
        return True


class BaseFundamentalProvider(ABC):
    """Abstract interface for fundamental / supply-demand data adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Vendor or agency human-readable name."""
        pass

    @abstractmethod
    def fetch_fundamental_observations(
        self,
        variable_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs,
    ) -> list[RawFundamentalObservation]:
        """Fetch fundamental time-series observations for a specific variable."""
        pass

    def is_healthy(self) -> bool:
        """Check provider connectivity and health status."""
        return True


class BaseCOTProvider(ABC):
    """Abstract interface for CFTC Commitment of Traders data adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Vendor or feed human-readable name."""
        pass

    @abstractmethod
    def fetch_cot_observations(
        self,
        commodity_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs,
    ) -> list[RawCOTObservation]:
        """Fetch institutional COT trader positioning observations."""
        pass

    def is_healthy(self) -> bool:
        """Check provider connectivity and health status."""
        return True
