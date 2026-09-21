"""
Serializers for Commodity Master, Deliverable Grade Chemistry, and Multi-Exchange Listings.
"""
from rest_framework import serializers
from apps.commodities.models import CommodityMaster, CommodityExchangeListing
from apps.exchanges.models import ExchangeMaster
from apps.metadata.models import UnitMaster


class NestedExchangeListingSerializer(serializers.ModelSerializer):
    """Nested venue serialization for multi-exchange listings."""
    exchange_code = serializers.CharField(source="exchange.code", read_only=True)
    exchange_name = serializers.CharField(source="exchange.name", read_only=True)
    exchange_mic = serializers.CharField(source="exchange.mic", read_only=True)
    exchange_country = serializers.CharField(source="exchange.country", read_only=True)
    contract_unit_code = serializers.CharField(source="contract_unit.code", read_only=True)
    contract_unit_symbol = serializers.CharField(source="contract_unit.symbol", read_only=True)

    class Meta:
        model = CommodityExchangeListing
        fields = (
            "id",
            "exchange_code",
            "exchange_name",
            "exchange_mic",
            "exchange_country",
            "ticker_symbol",
            "contract_size",
            "contract_unit_code",
            "contract_unit_symbol",
            "settlement_method",
            "is_primary_benchmark",
            "liquidity_tier",
            "typical_daily_volume",
            "typical_open_interest",
            "trading_currency",
            "is_active",
        )


class CommodityMasterListSerializer(serializers.ModelSerializer):
    """Compact summary serializer for commodity catalog listings."""
    primary_exchange_code = serializers.CharField(source="primary_exchange.code", read_only=True)
    primary_exchange_name = serializers.CharField(source="primary_exchange.name", read_only=True)
    base_unit_code = serializers.CharField(source="base_unit.code", read_only=True)
    base_unit_symbol = serializers.CharField(source="base_unit.symbol", read_only=True)
    pricing_unit_code = serializers.CharField(source="pricing_unit.code", read_only=True)
    pricing_unit_symbol = serializers.CharField(source="pricing_unit.symbol", read_only=True)
    exchange_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = CommodityMaster
        fields = (
            "id",
            "code",
            "name",
            "sector",
            "group",
            "primary_exchange_code",
            "primary_exchange_name",
            "base_unit_code",
            "base_unit_symbol",
            "pricing_unit_code",
            "pricing_unit_symbol",
            "standard_lot_size",
            "minimum_tick_size",
            "tick_value",
            "tick_currency",
            "settlement_method",
            "deliverable_grade_standard",
            "primary_delivery_hub",
            "crop_year_start_month",
            "exchange_count",
            "is_active",
            "display_order",
        )


class CommodityMasterDetailSerializer(serializers.ModelSerializer):
    """Full detailed serializer with deliverable chemistry, hubs, seasonality, and multi-exchange listings."""
    primary_exchange_code = serializers.CharField(source="primary_exchange.code", read_only=True)
    primary_exchange_name = serializers.CharField(source="primary_exchange.name", read_only=True)
    primary_exchange_mic = serializers.CharField(source="primary_exchange.mic", read_only=True)
    primary_exchange_timezone = serializers.CharField(source="primary_exchange.timezone", read_only=True)
    base_unit_code = serializers.CharField(source="base_unit.code", read_only=True)
    base_unit_symbol = serializers.CharField(source="base_unit.symbol", read_only=True)
    pricing_unit_code = serializers.CharField(source="pricing_unit.code", read_only=True)
    pricing_unit_symbol = serializers.CharField(source="pricing_unit.symbol", read_only=True)
    standard_lot_unit_code = serializers.CharField(source="standard_lot_unit.code", read_only=True)
    exchange_listings = NestedExchangeListingSerializer(many=True, read_only=True)

    class Meta:
        model = CommodityMaster
        fields = (
            "id",
            "code",
            "name",
            "sector",
            "group",
            "primary_exchange_code",
            "primary_exchange_name",
            "primary_exchange_mic",
            "primary_exchange_timezone",
            "base_unit_code",
            "base_unit_symbol",
            "pricing_unit_code",
            "pricing_unit_symbol",
            "standard_lot_size",
            "standard_lot_unit_code",
            "minimum_tick_size",
            "tick_value",
            "tick_currency",
            "settlement_method",
            "hs_code",
            "deliverable_grade_standard",
            "quality_specifications",
            "primary_delivery_hub",
            "delivery_hub_details",
            "crop_year_start_month",
            "peak_production_months",
            "peak_demand_months",
            "seasonality_notes",
            "description",
            "is_active",
            "display_order",
            "metadata",
            "exchange_listings",
        )
