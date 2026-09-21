"""
Factory resolver for Contract Specification Providers.

Enables dynamic provider swapping via Django settings or environment variables
without modifying any downstream quantitative models or API views.
"""

from importlib import import_module
import logging
from django.conf import settings
from .base import BaseContractSpecProvider
from .static_catalog import StaticContractSpecProvider

logger = logging.getLogger("apps.contracts")


def get_contract_provider() -> BaseContractSpecProvider:
    """
    Instantiate and return the active contract specification provider.
    Defaults to StaticContractSpecProvider (zero external dependencies).
    """
    provider_path = getattr(settings, "CONTRACT_SPEC_PROVIDER", None)

    if not provider_path or provider_path.lower() in ["static", "default"]:
        return StaticContractSpecProvider()

    try:
        module_path, class_name = provider_path.rsplit(".", 1)
        module = import_module(module_path)
        provider_class = getattr(module, class_name)
        provider_instance = provider_class()

        if not isinstance(provider_instance, BaseContractSpecProvider):
            raise TypeError(f"{provider_class} must implement BaseContractSpecProvider interface.")

        return provider_instance
    except Exception as exc:
        logger.error(
            f"Failed to load contract provider '{provider_path}': {exc}. Falling back to StaticContractSpecProvider."
        )
        return StaticContractSpecProvider()
