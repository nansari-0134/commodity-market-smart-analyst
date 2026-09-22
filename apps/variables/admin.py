"""
Django Admin configuration for Variable Master catalog.
"""

from django.contrib import admin
from apps.variables.models import VariableMaster


@admin.register(VariableMaster)
class VariableMasterAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "dataset",
        "commodity",
        "unit",
        "data_type",
        "aggregation_method",
        "is_benchmark",
        "is_active",
        "display_order",
    ]
    list_filter = [
        "is_benchmark",
        "is_active",
        "data_type",
        "aggregation_method",
        "domain",
        "dataset",
    ]
    search_fields = ["code", "name", "description"]
    ordering = ["display_order", "code"]
    raw_id_fields = ["dataset", "commodity", "domain", "unit"]
