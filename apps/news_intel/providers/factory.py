"""
Dynamic factory resolver for News & Market Intelligence Providers.
Supports 'static', 'rss', or custom class paths via settings.NEWS_PROVIDER.
"""

from typing import Type
from django.conf import settings
from django.utils.module_loading import import_string

from .base import BaseNewsProvider
from .static_data import StaticNewsProvider
from .rss_provider import RSSNewsProvider


def get_news_provider() -> BaseNewsProvider:
    """
    Resolve and instantiate the configured news & catalyst provider.
    Defaults to StaticNewsProvider for deterministic, offline-first reliability.
    """
    provider_setting = getattr(settings, "NEWS_PROVIDER", "static")

    if provider_setting == "static":
        return StaticNewsProvider()
    elif provider_setting == "rss":
        return RSSNewsProvider()

    try:
        provider_class: Type[BaseNewsProvider] = import_string(provider_setting)
        return provider_class()
    except (ImportError, AttributeError) as exc:
        raise ValueError(
            f"Failed to load news intelligence provider adapter '{provider_setting}': {exc}"
        ) from exc
