"""
Serializers for Exchange Master, Sessions, and Holiday Calendars.
"""
from rest_framework import serializers
from .models import ExchangeMaster, ExchangeTradingSession, ExchangeHoliday


class ExchangeTradingSessionSerializer(serializers.ModelSerializer):
    """Serializer for operating hours and settlement windows."""
    class Meta:
        model = ExchangeTradingSession
        fields = ("id", "session_type", "name", "start_time_local", "end_time_local", "days_of_week", "is_active")


class ExchangeHolidaySerializer(serializers.ModelSerializer):
    """Serializer for exchange holiday closures, sessions, and settlement status."""
    class Meta:
        model = ExchangeHoliday
        fields = (
            "id",
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


class ExchangeMasterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for exchange listing."""
    class Meta:
        model = ExchangeMaster
        fields = (
            "id",
            "code",
            "name",
            "mic",
            "operating_mic",
            "country",
            "city",
            "timezone",
            "currency",
            "tier",
            "website_url",
            "is_active",
        )


class ExchangeMasterDetailSerializer(serializers.ModelSerializer):
    """Full detailed serializer with inlined sessions and upcoming holidays."""
    sessions = ExchangeTradingSessionSerializer(many=True, read_only=True)
    holidays = ExchangeHolidaySerializer(many=True, read_only=True)

    class Meta:
        model = ExchangeMaster
        fields = (
            "id",
            "code",
            "name",
            "mic",
            "operating_mic",
            "country",
            "city",
            "timezone",
            "currency",
            "tier",
            "website_url",
            "is_active",
            "sessions",
            "holidays",
        )
