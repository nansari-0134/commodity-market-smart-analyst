"""
AppConfig for Narratives application.
"""
from django.apps import AppConfig


class NarrativesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.narratives"
    verbose_name = "AI Market Narratives & Hybrid Context"
