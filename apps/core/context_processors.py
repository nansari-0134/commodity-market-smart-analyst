"""
Context processors providing global platform metadata to templates.
"""
from django.conf import settings
from django.utils import timezone


def platform_context(request):
    """Exposes core application metadata and point-in-time reference."""
    return {
        "APP_NAME": getattr(settings, "APP_NAME", "Commodity Market Intelligence"),
        "APP_VERSION": getattr(settings, "APP_VERSION", "0.1.0-alpha"),
        "SERVER_TIME_UTC": timezone.now(),
        "CURRENT_PHASE": "Phase 1 - Django & Database Foundation",
    }
