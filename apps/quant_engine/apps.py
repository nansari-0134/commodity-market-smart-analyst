"""
Quantitative Research & Forward Curves Engine App Configuration.
"""
from django.apps import AppConfig


class QuantEngineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.quant_engine"
    verbose_name = "Quantitative Research & Forward Curves Engine"
