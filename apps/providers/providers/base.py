"""
Abstract base interfaces and DTOs for the Provider Catalog Provider Strategy.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class RawProviderSpec:
    """Normalized DTO representing a raw external data provider or internal engine."""

    code: str
    name: str
    description: str
    provider_type: str
    base_url: str
    documentation_url: str = ""
    support_contact: str = ""
    auth_type: str = "NONE_PUBLIC"
    env_var_name: str = ""
    auth_param_name: str = ""
    rate_limit_requests: Optional[int] = None
    rate_limit_window_seconds: int = 60
    backoff_seconds: int = 60
    target_sla_pct: float = 99.50
    fallback_code: Optional[str] = None
    is_active: bool = True
    display_order: int = 100
    notes: str = ""


class BaseProviderCatalogProvider(ABC):
    """Abstract interface defining the contract for all provider catalog adapters."""

    @abstractmethod
    def get_providers(self) -> List[RawProviderSpec]:
        """Return the complete list of normalized provider specifications."""
        pass

    @abstractmethod
    def get_provider(self, code: str) -> Optional[RawProviderSpec]:
        """Retrieve a single provider specification by unique canonical code."""
        pass
