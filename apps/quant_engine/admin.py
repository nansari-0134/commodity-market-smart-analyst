"""
Django Admin configuration for Quantitative Engine models.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.quant_engine.models import DiscoveryRegistry, EvidencePackageSnapshot


@admin.register(DiscoveryRegistry)
class DiscoveryRegistryAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "discovery_type",
        "commodity",
        "related_commodity",
        "as_of_date",
        "confidence_badge",
        "is_significant_badge",
        "is_active",
    ]
    list_filter = ["discovery_type", "commodity", "is_statistically_significant", "is_active"]
    search_fields = ["title", "commodity__code", "commodity__name", "notes"]
    date_hierarchy = "as_of_date"
    readonly_fields = ["created_at", "updated_at", "ingestion_time"]

    @admin.display(description="Confidence")
    def confidence_badge(self, obj):
        score = obj.confidence_score
        color = "green" if score >= 0.8 else ("orange" if score >= 0.5 else "red")
        return format_html('<span style="color: {}; font-weight: bold;">{:.1f}%</span>', color, score * 100)

    @admin.display(description="Significant?", boolean=True)
    def is_significant_badge(self, obj):
        return obj.is_statistically_significant


@admin.register(EvidencePackageSnapshot)
class EvidencePackageSnapshotAdmin(admin.ModelAdmin):
    list_display = ["commodity", "as_of_date", "engine_version", "created_at"]
    list_filter = ["commodity", "engine_version"]
    search_fields = ["commodity__code", "commodity__name"]
    date_hierarchy = "as_of_date"
    readonly_fields = ["created_at", "updated_at", "ingestion_time"]
