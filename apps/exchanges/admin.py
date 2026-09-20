"""
Django Admin configurations for Exchange Master, Sessions, and Holiday Calendars.
"""
from django.contrib import admin
from .models import ExchangeMaster, ExchangeTradingSession, ExchangeHoliday
from .services.holiday_service import ExchangeHolidaySyncService


class ExchangeTradingSessionInline(admin.TabularInline):
    model = ExchangeTradingSession
    extra = 1
    fields = ("name", "session_type", "start_time_local", "end_time_local", "days_of_week", "is_active")


class ExchangeHolidayInline(admin.TabularInline):
    model = ExchangeHoliday
    extra = 0
    fields = (
        "date",
        "name",
        "is_full_day_closure",
        "has_trading",
        "has_settlement",
        "settlement_rolled_to_next_day",
        "affected_product_groups",
        "early_close_time_local",
        "source_api",
        "is_active",
    )
    ordering = ("-date",)


@admin.register(ExchangeMaster)
class ExchangeMasterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "mic", "country", "city", "timezone", "currency", "tier", "is_active")
    list_filter = ("country", "tier", "currency", "is_active")
    search_fields = ("code", "name", "mic", "operating_mic", "city")
    ordering = ("code",)
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [ExchangeTradingSessionInline, ExchangeHolidayInline]
    actions = ["sync_holidays_action"]

    fieldsets = (
        ("Core Exchange Identity", {
            "fields": ("id", "code", "name", "mic", "operating_mic", "tier"),
        }),
        ("Location & Operating Conventions", {
            "fields": ("country", "city", "timezone", "currency", "website_url", "is_active"),
        }),
        ("Audit Trail", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.action(description="Fetch and sync holidays from reliable API")
    def sync_holidays_action(self, request, queryset):
        total_synced = 0
        for exchange in queryset:
            res = ExchangeHolidaySyncService.sync_exchange_holidays(exchange)
            total_synced += res["synced_count"]
        self.message_user(request, f"Successfully synchronized {total_synced} holidays across {queryset.count()} exchanges.")


@admin.register(ExchangeTradingSession)
class ExchangeTradingSessionAdmin(admin.ModelAdmin):
    list_display = ("exchange", "name", "session_type", "start_time_local", "end_time_local", "is_active")
    list_filter = ("session_type", "exchange", "is_active")
    search_fields = ("name", "exchange__code", "exchange__name")
    ordering = ("exchange", "start_time_local")


@admin.register(ExchangeHoliday)
class ExchangeHolidayAdmin(admin.ModelAdmin):
    list_display = (
        "exchange",
        "date",
        "name",
        "is_full_day_closure",
        "has_trading",
        "has_settlement",
        "settlement_rolled_to_next_day",
        "affected_product_groups",
        "early_close_time_local",
        "source_api",
        "is_active",
    )
    list_filter = (
        "exchange",
        "is_full_day_closure",
        "has_trading",
        "has_settlement",
        "settlement_rolled_to_next_day",
        "source_api",
        "is_active",
    )
    search_fields = ("name", "exchange__code", "exchange__name", "affected_product_groups")
    ordering = ("-date",)
