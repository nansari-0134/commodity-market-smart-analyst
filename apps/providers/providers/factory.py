"""
Dynamic factory resolver for Provider Catalog Provider.
"""

from typing import Type
from django.conf import settings
from django.utils.module_loading import import_string

from .base import BaseProviderCatalogProvider
from .static_catalog import StaticProviderCatalogProvider


def get_provider_catalog() -> BaseProviderCatalogProvider:
    """
    Resolve and instantiate the active Provider Catalog provider based on Django settings.
    Defaults to StaticProviderCatalogProvider for offline-first determinism.
    """
    provider_setting = getattr(settings, "PROVIDER_CATALOG_PROVIDER", "static")

    if provider_setting == "static":
        return StaticProviderCatalogProvider()

    # Dynamic class import for custom enterprise provider adapters
    try:
        provider_class: Type[BaseProviderCatalogProvider] = import_string(provider_setting)
        return provider_class()
    except (ImportError, AttributeError) as exc:
        raise ValueError(
            f"Failed to load provider catalog adapter '{provider_setting}': {exc}"
        ) from exc
