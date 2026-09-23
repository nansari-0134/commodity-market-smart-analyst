"""
Django Admin configuration for Provider Master Catalog.
"""

from django.contrib import admin
from django.utils.html import format_html

from apps.providers.models import ProviderMaster


@admin.register(ProviderMaster)
class ProviderMasterAdmin(admin.ModelAdmin):
    """Admin configuration for ProviderMaster with badges, filters, and grouped fieldsets."""

    list_display = [
        "code",
        "name",
        "provider_type_badge",
        "auth_type_badge",
        "rate_limit_display",
        "fallback_display",
        "target_sla_pct",
        "is_active",
    ]
    list_filter = [
        "provider_type",
        "auth_type",
        "is_active",
    ]
    search_fields = [
        "code",
        "name",
        "description",
        "env_var_name",
    ]
    ordering = ["display_order", "code"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            "Provider Identification & Classification",
            {
                "fields": (
                    "code",
                    "name",
                    "provider_type",
                    "description",
                    "base_url",
                    "documentation_url",
                    "support_contact",
                )
            },
        ),
        (
            "12-Factor Security & Authentication",
            {
                "description": "Credentials reference environment variables. Never store raw secrets in the database.",
                "fields": (
                    "auth_type",
                    "env_var_name",
                    "auth_param_name",
                ),
            },
        ),
        (
            "Rate Limiting & Backoff Policies",
            {
                "fields": (
                    "rate_limit_requests",
                    "rate_limit_window_seconds",
                    "backoff_seconds",
                )
            },
        ),
        (
            "Redundancy, SLA & Operational Governance",
            {
                "fields": (
                    "target_sla_pct",
                    "fallback_provider",
                    "is_active",
                    "display_order",
                    "notes",
                    "id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Provider Type")
    def provider_type_badge(self, obj: ProviderMaster) -> str:
        colors = {
            "GOVERNMENT_PUBLIC": "#0d6efd",
            "EXCHANGE_DIRECT": "#198754",
            "PRICE_REPORTING_AGENCY": "#fd7e14",
            "COMMERCIAL_AGGREGATOR": "#6f42c1",
            "ALTERNATIVE_DATA": "#20c997",
            "INTERNAL_ENGINE": "#6c757d",
        }
        color = colors.get(obj.provider_type, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 500; font-size: 11px;">{}</span>',
            color,
            obj.get_provider_type_display(),
        )

    @admin.display(description="Auth Protocol")
    def auth_type_badge(self, obj: ProviderMaster) -> str:
        if obj.auth_type == "NONE_PUBLIC":
            return format_html('<span style="color: #198754; font-weight: 500;">Public Open Data</span>')
        return format_html(
            '<span style="font-family: monospace; font-weight: 600; color: #495057;">{} ({})</span>',
            obj.get_auth_type_display(),
            obj.env_var_name or "N/A",
        )

    @admin.display(description="Rate Budget")
    def rate_limit_display(self, obj: ProviderMaster) -> str:
        if obj.rate_limit_requests is not None:
            return f"{obj.rate_limit_requests:,} req / {obj.rate_limit_window_seconds}s"
        return "Unmetered"

    @admin.display(description="Failover Target")
    def fallback_display(self, obj: ProviderMaster) -> str:
        if obj.fallback_provider:
            return f"➔ {obj.fallback_provider.code}"
        return "None"
