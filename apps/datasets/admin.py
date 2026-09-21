"""
Django Admin Configuration for Dataset Master Catalog.
"""

from django.contrib import admin
from apps.datasets.models import DatasetMaster


@admin.register(DatasetMaster)
class DatasetMasterAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "domain",
        "frequency",
        "data_category",
        "update_cadence",
        "ingestion_mode",
        "license_type",
        "source_authority",
        "sla_max_delay_minutes",
        "is_active",
    ]
    list_filter = [
        "data_category",
        "update_cadence",
        "ingestion_mode",
        "license_type",
        "domain",
        "frequency",
        "is_active",
    ]
    search_fields = [
        "code",
        "name",
        "source_authority",
        "description",
    ]
    filter_horizontal = ["commodities"]
    ordering = ["display_order", "code"]
