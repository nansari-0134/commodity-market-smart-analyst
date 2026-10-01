"""
News & Market Intelligence App Config.
"""
from django.apps import AppConfig


class NewsIntelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.news_intel"
    verbose_name = "News & Market Intelligence"
