"""
Django Admin configuration for Endpoint Master Catalog.
"""

from django.contrib import admin
from django.utils.html import format_html

from apps.endpoints.models import EndpointMaster


@admin.register(EndpointMaster)
class EndpointMasterAdmin(admin.ModelAdmin):
    """Admin configuration for EndpointMaster with badges, filters, and grouped fieldsets."""

    list_display = [
        "code",
        "name",
        "provider_link",
        "dataset_link",
        "http_method_badge",
        "protocol_badge",
        "response_format_badge",
        "cache_ttl_display",
        "is_active",
        "is_deprecated",
    ]
    list_filter = [
        "protocol",
        "http_method",
        "response_format",
        "is_active",
        "is_deprecated",
        "provider",
    ]
    search_fields = [
        "code",
        "name",
        "path_template",
        "description",
        "provider__code",
        "provider__name",
        "dataset__code",
        "dataset__name",
    ]
    ordering = ["provider__code", "code"]
    readonly_fields = ["id", "full_url_preview", "created_at", "updated_at"]
    list_select_related = ["provider", "dataset"]

    fieldsets = (
        (
            "Endpoint Identification & Bindings",
            {
                "fields": (
                    "code",
                    "name",
                    "description",
                    "provider",
                    "dataset",
                )
            },
        ),
        (
            "Transport Protocol & Route Template",
            {
                "description": "Defines network protocol, HTTP method, and relative path template.",
                "fields": (
                    "protocol",
                    "http_method",
                    "path_template",
                    "full_url_preview",
                ),
            },
        ),
        (
            "Payload Format & Envelope Extraction",
            {
                "fields": (
                    "response_format",
                    "data_envelope_path",
                ),
            },
        ),
        (
            "Parameter Schemas & Request Headers",
            {
                "description": "Consolidated query parameter defaults and custom HTTP request headers.",
                "fields": (
                    "default_params",
                    "custom_headers",
                ),
            },
        ),
        (
            "Caching & Operational Lifecycle",
            {
                "fields": (
                    "cache_ttl_seconds",
                    "is_active",
                    "is_deprecated",
                    "notes",
                    "id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Provider")
    def provider_link(self, obj: EndpointMaster) -> str:
        return format_html(
            '<span style="font-weight: 600; color: #0d6efd;">{}</span>',
            obj.provider.code,
        )

    @admin.display(description="Dataset")
    def dataset_link(self, obj: EndpointMaster) -> str:
        if obj.dataset:
            return format_html(
                '<span style="font-family: monospace; font-size: 11px; color: #198754;">{}</span>',
                obj.dataset.code,
            )
        return format_html('<span style="color: #6c757d; font-style: italic;">None</span>')

    @admin.display(description="Method")
    def http_method_badge(self, obj: EndpointMaster) -> str:
        colors = {
            "GET": "#0d6efd",
            "POST": "#198754",
        }
        color = colors.get(obj.http_method, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 7px; border-radius: 3px; font-weight: 700; font-size: 11px; font-family: monospace;">{}</span>',
            color,
            obj.http_method,
        )

    @admin.display(description="Protocol")
    def protocol_badge(self, obj: EndpointMaster) -> str:
        colors = {
            "REST_HTTP": "#6f42c1",
            "FTP_SFTP": "#fd7e14",
            "WEBSOCKET": "#20c997",
        }
        color = colors.get(obj.protocol, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 7px; border-radius: 3px; font-weight: 500; font-size: 11px;">{}</span>',
            color,
            obj.get_protocol_display(),
        )

    @admin.display(description="Format")
    def response_format_badge(self, obj: EndpointMaster) -> str:
        return format_html(
            '<span style="background-color: #212529; color: #ffc107; padding: 2px 6px; border-radius: 3px; font-weight: 600; font-size: 11px; font-family: monospace;">{}</span>',
            obj.response_format,
        )

    @admin.display(description="Cache TTL")
    def cache_ttl_display(self, obj: EndpointMaster) -> str:
        if obj.cache_ttl_seconds >= 86400:
            return f"{obj.cache_ttl_seconds // 86400}d"
        if obj.cache_ttl_seconds >= 3600:
            return f"{obj.cache_ttl_seconds // 3600}h"
        return f"{obj.cache_ttl_seconds}s"

    @admin.display(description="Full URL Preview")
    def full_url_preview(self, obj: EndpointMaster) -> str:
        if not obj.pk:
            return "Save model first to resolve full URL."
        full_url = obj.get_full_url()
        return format_html(
            '<code style="background-color: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-size: 12px; color: #d63384;">{}</code>',
            full_url,
        )
