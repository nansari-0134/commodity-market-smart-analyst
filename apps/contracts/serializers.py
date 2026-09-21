"""
REST API Serializers for Contract Master and Derivatives.
"""

from rest_framework import serializers
from apps.contracts.models import (
    ContractSpecification,
    ContractExpiry,
    InstrumentType,
    ExpiryRuleType,
    SettlementMethod,
    MonthCode,
)


class ContractExpirySerializer(serializers.ModelSerializer):
    """Serializer for individual tradable contract delivery months."""

    specification_symbol = serializers.CharField(source="specification.symbol_root", read_only=True)
    exchange_mic = serializers.CharField(source="specification.exchange.mic", read_only=True)
    exchange_code = serializers.CharField(source="specification.exchange.code", read_only=True)

    class Meta:
        model = ContractExpiry
        fields = [
            "id",
            "contract_symbol",
            "specification_symbol",
            "exchange_mic",
            "exchange_code",
            "contract_year",
            "contract_month",
            "contract_month_code",
            "last_trading_day",
            "first_notice_day",
            "last_delivery_day",
            "final_settlement_date",
            "is_expired",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ContractSpecificationListSerializer(serializers.ModelSerializer):
    """Compact serializer for listing contract specifications."""

    commodity_code = serializers.CharField(source="commodity.code", read_only=True)
    commodity_name = serializers.CharField(source="commodity.name", read_only=True)
    exchange_code = serializers.CharField(source="exchange.code", read_only=True)
    exchange_mic = serializers.CharField(source="exchange.mic", read_only=True)
    contract_unit_code = serializers.CharField(source="contract_unit.code", read_only=True)
    price_quote_unit_code = serializers.CharField(source="price_quote_unit.code", read_only=True)
    active_expiries_count = serializers.IntegerField(source="expiries.count", read_only=True)

    class Meta:
        model = ContractSpecification
        fields = [
            "id",
            "symbol_root",
            "name",
            "commodity_code",
            "commodity_name",
            "exchange_code",
            "exchange_mic",
            "instrument_type",
            "contract_size",
            "contract_unit_code",
            "price_quote_unit_code",
            "minimum_tick_size",
            "tick_value",
            "trading_currency",
            "settlement_method",
            "trading_months",
            "expiry_rule",
            "default_roll_rule",
            "active_expiries_count",
            "is_active",
            "display_order",
        ]


class ContractSpecificationDetailSerializer(ContractSpecificationListSerializer):
    """Full detail serializer with nested prompt delivery contract expiries."""

    expiries = ContractExpirySerializer(many=True, read_only=True)

    class Meta(ContractSpecificationListSerializer.Meta):
        fields = ContractSpecificationListSerializer.Meta.fields + [
            "expiry_rule_parameter",
            "notice_rule",
            "expiries",
            "created_at",
            "updated_at",
        ]


class ContractSummarySerializer(serializers.Serializer):
    """Statistical summary of derivative contracts and prompt curve maturities."""

    total_specifications = serializers.IntegerField()
    total_expiries = serializers.IntegerField()
    active_expiries = serializers.IntegerField()
    expired_contracts = serializers.IntegerField()
    settlement_method_breakdown = serializers.DictField()
    instrument_type_breakdown = serializers.DictField()
    exchange_breakdown = serializers.DictField()
