"""
Factory resolver for Dataset Catalog Providers.

Enables dynamic provider swapping via Django settings or environment variables
without modifying any downstream data pipeline or analytical models.
"""

from importlib import import_module
import logging
from django.conf import settings
from .base import BaseDatasetCatalogProvider
from .static_catalog import StaticDatasetCatalogProvider

logger = logging.getLogger("apps.datasets")


def get_dataset_provider() -> BaseDatasetCatalogProvider:
    """
    Instantiate and return the active dataset catalog provider.
    Defaults to StaticDatasetCatalogProvider (zero external dependencies).
    """
    provider_path = getattr(settings, "DATASET_CATALOG_PROVIDER", None)

    if not provider_path or provider_path.lower() in ["static", "default"]:
        return StaticDatasetCatalogProvider()

    try:
        module_path, class_name = provider_path.rsplit(".", 1)
        module = import_module(module_path)
        provider_class = getattr(module, class_name)
        provider_instance = provider_class()

        if not isinstance(provider_instance, BaseDatasetCatalogProvider):
            raise TypeError(f"{provider_class} must implement BaseDatasetCatalogProvider interface.")

        return provider_instance
    except Exception as exc:
        logger.error(
            f"Failed to load dataset provider '{provider_path}': {exc}. Falling back to StaticDatasetCatalogProvider."
        )
        return StaticDatasetCatalogProvider()
