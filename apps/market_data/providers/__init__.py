"""
Pluggable Market Data Providers.
Implements the Strategy + Factory pattern for source-independent ingestion.
"""
from .base import (
    BaseMarketDataProvider,
    BaseFundamentalProvider,
    BaseCOTProvider,
    RawPriceObservation,
    RawFundamentalObservation,
    RawCOTObservation,
)
from .factory import (
    get_market_data_provider,
    get_fundamental_provider,
    get_cot_provider,
    register_market_data_provider,
    register_fundamental_provider,
    register_cot_provider,
)

__all__ = [
    "BaseMarketDataProvider",
    "BaseFundamentalProvider",
    "BaseCOTProvider",
    "RawPriceObservation",
    "RawFundamentalObservation",
    "RawCOTObservation",
    "get_market_data_provider",
    "get_fundamental_provider",
    "get_cot_provider",
    "register_market_data_provider",
    "register_fundamental_provider",
    "register_cot_provider",
]
