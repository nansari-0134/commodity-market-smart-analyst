"""
Dynamic factory resolver for Endpoint Catalog Provider.
"""

from typing import Type
from django.conf import settings
from django.utils.module_loading import import_string

from .base import BaseEndpointCatalogProvider
from .static_catalog import StaticEndpointCatalogProvider


def get_endpoint_catalog() -> BaseEndpointCatalogProvider:
    """
    Resolve and instantiate the active Endpoint Catalog provider based on Django settings.
    Defaults to StaticEndpointCatalogProvider for offline-first determinism.
    """
    provider_setting = getattr(settings, "ENDPOINT_CATALOG_PROVIDER", "static")

    if provider_setting == "static":
        return StaticEndpointCatalogProvider()

    # Dynamic class import for custom enterprise provider adapters
    try:
        provider_class: Type[BaseEndpointCatalogProvider] = import_string(provider_setting)
        return provider_class()
    except (ImportError, AttributeError) as exc:
        raise ValueError(
            f"Failed to load endpoint catalog adapter '{provider_setting}': {exc}"
        ) from exc
