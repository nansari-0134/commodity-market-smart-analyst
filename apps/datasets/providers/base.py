"""
Base Dataset Catalog Provider Interface and Data Transfer Objects (DTOs).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class RawDatasetSpec:
    """Strongly-typed DTO representing a canonical dataset catalog specification."""

    code: str
    name: str
    description: str
    domain_code: str
    frequency_code: str
    source_authority: str
    data_category: str = "MARKET_PRICES"
    update_cadence: str = "DAILY_EOD"
    ingestion_mode: str = "PULL_SCHEDULED_BATCH"
    release_schedule: Dict[str, Any] = field(default_factory=dict)
    primary_commodity_code: Optional[str] = None
    commodity_codes: List[str] = field(default_factory=list)
    exchange_code: Optional[str] = None
    retention_policy: str = "INDEFINITE_POINT_IN_TIME"
    license_type: str = "PUBLIC_DOMAIN"
    point_in_time_enabled: bool = True
    supports_revisions: bool = True
    sla_max_delay_minutes: int = 60
    documentation_url: str = ""
    display_order: int = 100


class BaseDatasetCatalogProvider(ABC):
    """
    Abstract interface for dataset master catalog feeds.
    Enforces pluggable, vendor-agnostic resolution of dataset catalog metadata.
    """

    @abstractmethod
    def get_datasets(self) -> List[RawDatasetSpec]:
        """Fetch all canonical dataset specifications."""
        pass

    @abstractmethod
    def get_dataset(self, code: str) -> Optional[RawDatasetSpec]:
        """Retrieve a single dataset specification by code."""
        pass
