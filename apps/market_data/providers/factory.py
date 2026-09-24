"""
Factory and Provider Registry for Market Data & Time-Series Observations.

Enforces Core Directive 1: Pluggable Source Independence.
Data providers are resolved dynamically based on Django settings or .env configuration,
allowing developers to swap simulated, test, or production vendors with zero changes to
downstream analytical code or database models.
"""

from typing import Type
from django.conf import settings

from .base import BaseMarketDataProvider, BaseFundamentalProvider, BaseCOTProvider
from .static_data import (
    StaticMarketDataProvider,
    StaticFundamentalProvider,
    StaticCOTProvider,
)

# In-memory registries for pluggable providers
_MARKET_DATA_PROVIDERS: dict[str, Type[BaseMarketDataProvider]] = {
    "static": StaticMarketDataProvider,
}

_FUNDAMENTAL_PROVIDERS: dict[str, Type[BaseFundamentalProvider]] = {
    "static": StaticFundamentalProvider,
}

_COT_PROVIDERS: dict[str, Type[BaseCOTProvider]] = {
    "static": StaticCOTProvider,
}


def register_market_data_provider(name: str, provider_cls: Type[BaseMarketDataProvider]) -> None:
    """Register a new market data provider class under a key."""
    _MARKET_DATA_PROVIDERS[name.lower()] = provider_cls


def register_fundamental_provider(name: str, provider_cls: Type[BaseFundamentalProvider]) -> None:
    """Register a new fundamental data provider class under a key."""
    _FUNDAMENTAL_PROVIDERS[name.lower()] = provider_cls


def register_cot_provider(name: str, provider_cls: Type[BaseCOTProvider]) -> None:
    """Register a new CFTC COT data provider class under a key."""
    _COT_PROVIDERS[name.lower()] = provider_cls


def get_market_data_provider(name: str | None = None) -> BaseMarketDataProvider:
    """
    Instantiate and return the configured market data provider.
    Defaults to settings.MARKET_DATA_PROVIDER or 'static'.
    """
    key = (name or getattr(settings, "MARKET_DATA_PROVIDER", "static")).lower()
    provider_cls = _MARKET_DATA_PROVIDERS.get(key)
    if not provider_cls:
        available = ", ".join(_MARKET_DATA_PROVIDERS.keys())
        raise ValueError(f"Unknown market data provider '{key}'. Available providers: {available}")
    return provider_cls()


def get_fundamental_provider(name: str | None = None) -> BaseFundamentalProvider:
    """
    Instantiate and return the configured fundamental data provider.
    Defaults to settings.FUNDAMENTAL_DATA_PROVIDER or 'static'.
    """
    key = (name or getattr(settings, "FUNDAMENTAL_DATA_PROVIDER", "static")).lower()
    provider_cls = _FUNDAMENTAL_PROVIDERS.get(key)
    if not provider_cls:
        available = ", ".join(_FUNDAMENTAL_PROVIDERS.keys())
        raise ValueError(f"Unknown fundamental data provider '{key}'. Available providers: {available}")
    return provider_cls()


def get_cot_provider(name: str | None = None) -> BaseCOTProvider:
    """
    Instantiate and return the configured COT data provider.
    Defaults to settings.COT_DATA_PROVIDER or 'static'.
    """
    key = (name or getattr(settings, "COT_DATA_PROVIDER", "static")).lower()
    provider_cls = _COT_PROVIDERS.get(key)
    if not provider_cls:
        available = ", ".join(_COT_PROVIDERS.keys())
        raise ValueError(f"Unknown COT data provider '{key}'. Available providers: {available}")
    return provider_cls()
