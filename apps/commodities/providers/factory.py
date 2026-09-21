"""
Provider Factory for Commodity Reference Data.
Instantiates active catalog provider based on Django settings / environment variables.
"""
from django.conf import settings
from .base import BaseCommodityCatalogProvider
from .static_catalog import StaticCommodityCatalogProvider


def get_commodity_provider() -> BaseCommodityCatalogProvider:
    """
    Factory resolver returning the configured commodity catalog provider.
    Defaults to StaticCommodityCatalogProvider.
    """
    provider_type = getattr(settings, "COMMODITY_CATALOG_PROVIDER", "static").lower()

    if provider_type in ("static", "default", "offline"):
        return StaticCommodityCatalogProvider()

    # Future institutional adapters (e.g. cme_datamine, refinitiv) can be registered here:
    # elif provider_type == "cme_datamine":
    #     from .cme_provider import CMEDatamineProvider
    #     return CMEDatamineProvider()

    # Default fallback to static catalog
    return StaticCommodityCatalogProvider()
