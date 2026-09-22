"""
Factory resolver for Variable Catalog Providers.
"""

from django.conf import settings
from django.utils.module_loading import import_string

from apps.variables.providers.base import BaseVariableCatalogProvider
from apps.variables.providers.static_catalog import StaticVariableCatalogProvider


def get_variable_provider() -> BaseVariableCatalogProvider:
    """
    Resolves and instantiates the configured Variable Catalog Provider.
    Defaults to StaticVariableCatalogProvider if unset or set to 'static'.
    """
    provider_setting = getattr(settings, "VARIABLE_CATALOG_PROVIDER", "static")

    if provider_setting == "static":
        return StaticVariableCatalogProvider()

    try:
        provider_class = import_string(provider_setting)
        return provider_class()
    except (ImportError, AttributeError):
        return StaticVariableCatalogProvider()
