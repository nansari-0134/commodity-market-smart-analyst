"""
Django Admin Configuration for Commodity Master and Multi-Exchange Listings.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.commodities.models import CommodityMaster, CommodityExchangeListing


class CommodityExchangeListingInline(admin.TabularInline):
    """Inlined table of exchange listings directly inside CommodityMaster admin."""
    model = CommodityExchangeListing
    extra = 1
    fields = (
        "exchange",
        "ticker_symbol",
        "contract_size",
        "contract_unit",
        "settlement_method",
        "is_primary_benchmark",
        "liquidity_tier",
        "typical_daily_volume",
        "typical_open_interest",
        "trading_currency",
        "is_active",
    )


@admin.register(CommodityMaster)
class CommodityMasterAdmin(admin.ModelAdmin):
    """Admin console for Canonical Commodity Master."""
    list_display = (
        "code",
        "name",
        "sector_badge",
        "group",
        "primary_exchange",
        "base_unit",
        "pricing_unit",
        "settlement_method",
        "exchange_count_display",
        "primary_delivery_hub",
        "crop_year_start_month",
        "is_active",
    )
    list_filter = ("sector", "group", "primary_exchange", "settlement_method", "is_active")
    search_fields = ("code", "name", "deliverable_grade_standard", "primary_delivery_hub", "hs_code")
    ordering = ("sector", "display_order", "code")
    inlines = [CommodityExchangeListingInline]

    fieldsets = (
        (
            "Classification & Venues",
            {
                "fields": (
                    "code",
                    "name",
                    "sector",
                    "group",
                    "primary_exchange",
                    "is_active",
                    "display_order",
                )
            },
        ),
        (
            "Benchmark Units & Tick Specs",
            {
                "fields": (
                    "base_unit",
                    "pricing_unit",
                    "standard_lot_size",
                    "standard_lot_unit",
                    "minimum_tick_size",
                    "tick_value",
                    "tick_currency",
                    "settlement_method",
                    "hs_code",
                )
            },
        ),
        (
            "Deliverable Grade & Chemistry",
            {
                "fields": (
                    "deliverable_grade_standard",
                    "quality_specifications",
                )
            },
        ),
        (
            "Delivery Hub Infrastructure",
            {
                "fields": (
                    "primary_delivery_hub",
                    "delivery_hub_details",
                )
            },
        ),
        (
            "Crop & Production Seasonality",
            {
                "fields": (
                    "crop_year_start_month",
                    "peak_production_months",
                    "peak_demand_months",
                    "seasonality_notes",
                )
            },
        ),
        (
            "Commercial Scope & Metadata",
            {
                "classes": ("collapse",),
                "fields": ("description", "metadata"),
            },
        ),
    )

    def sector_badge(self, obj):
        colors = {
            "ENERGY": "#ef4444",
            "AGRICULTURE": "#10b981",
            "LIVESTOCK": "#f59e0b",
            "METALS_BASE": "#06b6d4",
            "METALS_PRECIOUS": "#eab308",
            "FREIGHT_BULK": "#8b5cf6",
            "ENVIRONMENTAL": "#14b8a6",
        }
        color = colors.get(obj.sector, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#ffffff; padding:2px 8px; border-radius:4px; font-weight:600; font-size:0.75rem;">{}</span>',
            color,
            obj.sector,
        )
    sector_badge.short_description = "Sector"

    def exchange_count_display(self, obj):
        count = obj.exchange_count
        return format_html(
            '<span style="font-weight:600; color:#3b82f6;">{} Venues</span>',
            count,
        )
    exchange_count_display.short_description = "Listings"


@admin.register(CommodityExchangeListing)
class CommodityExchangeListingAdmin(admin.ModelAdmin):
    """Admin console for Multi-Exchange Commodity Listings."""
    list_display = (
        "ticker_symbol",
        "commodity",
        "exchange",
        "contract_size",
        "contract_unit",
        "settlement_method",
        "is_primary_benchmark",
        "liquidity_tier",
        "typical_daily_volume",
        "typical_open_interest",
        "trading_currency",
        "is_active",
    )
    list_filter = ("exchange", "settlement_method", "liquidity_tier", "is_primary_benchmark", "is_active")
    search_fields = ("ticker_symbol", "commodity__code", "commodity__name", "exchange__code")
    ordering = ("commodity", "-is_primary_benchmark", "-typical_daily_volume")
