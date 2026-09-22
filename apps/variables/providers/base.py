"""
Base Variable Catalog Provider Interface and Data Transfer Objects (DTOs).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class RawVariableSpec:
    """Strongly-typed DTO representing a canonical metric/variable specification."""

    code: str
    name: str
    description: str
    dataset_code: str
    domain_code: str
    unit_code: str
    commodity_code: Optional[str] = None
    data_type: str = "DECIMAL"
    aggregation_method: str = "LAST"
    seasonal_adjustment: str = "UNADJUSTED"
    default_transformation: str = "RAW_LEVEL"
    is_benchmark: bool = False
    display_order: int = 100


class BaseVariableCatalogProvider(ABC):
    """
    Abstract interface for variable catalog feeds.
    Enforces pluggable, vendor-agnostic resolution of metric metadata.
    """

    @abstractmethod
    def get_variables(self) -> List[RawVariableSpec]:
        """Fetch all canonical variable specifications."""
        pass

    @abstractmethod
    def get_variable(self, code: str) -> Optional[RawVariableSpec]:
        """Retrieve a single variable specification by code."""
        pass
