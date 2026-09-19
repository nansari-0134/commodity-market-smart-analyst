"""
Django Admin configurations for metadata taxonomy masters.
"""
from django.contrib import admin
from .models import DataDomainMaster, UnitMaster, FrequencyMaster


@admin.register(DataDomainMaster)
class DataDomainMasterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "parent", "display_order", "is_active", "updated_at")
    list_filter = ("category", "is_active", "parent")
    search_fields = ("code", "name", "description")
    ordering = ("category", "display_order", "name")
    list_editable = ("display_order", "is_active")
    readonly_fields = ("id", "created_at", "updated_at", "hierarchy_path")
    fieldsets = (
        ("Core Identity", {
            "fields": ("id", "code", "name", "category", "parent", "hierarchy_path"),
        }),
        ("Scope & Metadata", {
            "fields": ("description", "display_order", "is_active"),
        }),
        ("Audit Trail", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(UnitMaster)
class UnitMasterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol", "unit_type", "base_unit", "conversion_factor", "is_active")
    list_filter = ("unit_type", "is_active")
    search_fields = ("code", "name", "symbol", "description")
    ordering = ("unit_type", "code")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        ("Unit Specifications", {
            "fields": ("id", "code", "name", "symbol", "unit_type"),
        }),
        ("Conversion Rules", {
            "fields": ("base_unit", "conversion_factor", "description"),
        }),
        ("Status & Audit", {
            "fields": ("is_active", "created_at", "updated_at"),
        }),
    )


@admin.register(FrequencyMaster)
class FrequencyMasterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "standard_interval_seconds", "is_regular", "is_active")
    list_filter = ("is_regular", "is_active")
    search_fields = ("code", "name", "description")
    ordering = ("standard_interval_seconds", "name")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        ("Frequency Definition", {
            "fields": ("id", "code", "name", "standard_interval_seconds", "is_regular"),
        }),
        ("Operational Cadence", {
            "fields": ("description", "is_active", "created_at", "updated_at"),
        }),
    )
