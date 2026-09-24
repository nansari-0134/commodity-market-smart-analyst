"""
Django Admin Configuration for Market Data & Time-Series Observations.
"""

from django.contrib import admin
from django.utils.html import format_html

from apps.market_data.models import (
    MarketPriceObservation,
    FundamentalObservation,
    CommitmentOfTradersObservation,
)


@admin.register(MarketPriceObservation)
class MarketPriceObservationAdmin(admin.ModelAdmin):
    list_display = [
        "commodity",
        "delivery_month",
        "is_prompt_badge",
        "observation_date",
        "settlement_price",
        "close_price",
        "volume",
        "open_interest",
        "quality_status",
    ]
    list_filter = ["commodity", "is_prompt", "quality_status", "delivery_month"]
    search_fields = ["commodity__code", "commodity__name", "delivery_month"]
    date_hierarchy = "observation_date"
    readonly_fields = ["created_at", "updated_at", "ingestion_time"]

    @admin.display(description="Prompt?", boolean=True)
    def is_prompt_badge(self, obj):
        return obj.is_prompt


@admin.register(FundamentalObservation)
class FundamentalObservationAdmin(admin.ModelAdmin):
    list_display = [
        "variable",
        "observation_date",
        "value",
        "unit",
        "period_start",
        "period_end",
        "is_preliminary",
        "quality_status",
    ]
    list_filter = ["variable", "is_preliminary", "quality_status"]
    search_fields = ["variable__code", "variable__name"]
    date_hierarchy = "observation_date"
    readonly_fields = ["created_at", "updated_at", "ingestion_time"]


@admin.register(CommitmentOfTradersObservation)
class CommitmentOfTradersObservationAdmin(admin.ModelAdmin):
    list_display = [
        "commodity",
        "observation_date",
        "report_type",
        "open_interest",
        "money_manager_net_display",
        "commercial_net_display",
        "quality_status",
    ]
    list_filter = ["commodity", "report_type", "quality_status"]
    search_fields = ["commodity__code", "commodity__name"]
    date_hierarchy = "observation_date"
    readonly_fields = ["created_at", "updated_at", "ingestion_time"]

    @admin.display(description="MM Net (Pct OI)")
    def money_manager_net_display(self, obj):
        net = obj.money_manager_net
        color = "green" if net > 0 else "red"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:+d} ({:.1f}%)</span>',
            color,
            net,
            obj.money_manager_net_pct_oi,
        )

    @admin.display(description="Commercial Net")
    def commercial_net_display(self, obj):
        net = obj.commercial_net
        color = "blue" if net > 0 else "orange"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:+d} ({:.1f}%)</span>',
            color,
            net,
            obj.commercial_net_pct_oi,
        )
