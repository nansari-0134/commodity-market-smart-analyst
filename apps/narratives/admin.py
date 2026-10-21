"""
Django admin registration for MarketNarrative.
"""
from django.contrib import admin
from .models import MarketNarrative


@admin.register(MarketNarrative)
class MarketNarrativeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "commodity",
        "narrative_type",
        "headline",
        "llm_provider",
        "llm_model",
        "status",
        "availability_time",
    )
    list_filter = ("narrative_type", "status", "llm_provider", "commodity")
    search_fields = ("headline", "executive_summary", "market_context_body")
    readonly_fields = (
        "id",
        "availability_time",
        "ingestion_time",
        "evidence_snapshot",
        "compliance_disclaimer",
    )
    date_hierarchy = "availability_time"
