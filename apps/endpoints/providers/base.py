"""
Abstract base interfaces and DTOs for the Endpoint Catalog Provider Strategy.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RawEndpointSpec:
    """Normalized DTO representing a vendor API endpoint specification."""

    code: str
    name: str
    description: str
    provider_code: str
    dataset_code: Optional[str] = None
    protocol: str = "REST_HTTP"
    http_method: str = "GET"
    path_template: str = ""
    response_format: str = "JSON"
    data_envelope_path: str = ""
    default_params: Dict = field(default_factory=dict)
    custom_headers: Dict = field(default_factory=dict)
    cache_ttl_seconds: int = 3600
    is_active: bool = True
    notes: str = ""


class BaseEndpointCatalogProvider(ABC):
    """Abstract interface defining the contract for all endpoint catalog adapters."""

    @abstractmethod
    def get_endpoints(self) -> List[RawEndpointSpec]:
        """Return the complete list of normalized endpoint specifications."""
        pass

    @abstractmethod
    def get_endpoint(self, code: str) -> Optional[RawEndpointSpec]:
        """Retrieve a single endpoint specification by unique canonical code."""
        pass
