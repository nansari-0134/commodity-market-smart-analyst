"""
REST API Serializers for Market Data & Time-Series Observations.
"""

from rest_framework import serializers

from apps.market_data.models import (
    MarketPriceObservation,
    FundamentalObservation,
    CommitmentOfTradersObservation,
)


class MarketPriceObservationSerializer(serializers.ModelSerializer):
    """Serializer for commodity market price bars and exchange settlements."""

    commodity_code = serializers.CharField(source="commodity.code", read_only=True)
    commodity_name = serializers.CharField(source="commodity.name", read_only=True)
    contract_symbol = serializers.CharField(source="contract.symbol_root", read_only=True, default=None)
    endpoint_code = serializers.CharField(source="source_endpoint.code", read_only=True, default=None)
    price = serializers.DecimalField(max_digits=18, decimal_places=6, read_only=True)
    display_settlement = serializers.CharField(read_only=True)

    class Meta:
        model = MarketPriceObservation
        fields = [
            "id",
            "commodity_code",
            "commodity_name",
            "contract_symbol",
            "delivery_month",
            "is_prompt",
            "observation_date",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "settlement_price",
            "price",
            "display_settlement",
            "volume",
            "open_interest",
            "quality_status",
            "endpoint_code",
            "publication_time",
            "availability_time",
            "is_preliminary",
            "revision_number",
            "created_at",
        ]


class FundamentalObservationSerializer(serializers.ModelSerializer):
    """Serializer for fundamental supply-demand and inventory time series."""

    variable_code = serializers.CharField(source="variable.code", read_only=True)
    variable_name = serializers.CharField(source="variable.name", read_only=True)
    unit_code = serializers.CharField(source="unit.code", read_only=True, default=None)
    endpoint_code = serializers.CharField(source="source_endpoint.code", read_only=True, default=None)
    display_value = serializers.CharField(read_only=True)

    class Meta:
        model = FundamentalObservation
        fields = [
            "id",
            "variable_code",
            "variable_name",
            "observation_date",
            "value",
            "display_value",
            "unit_code",
            "period_start",
            "period_end",
            "quality_status",
            "endpoint_code",
            "publication_time",
            "availability_time",
            "is_preliminary",
            "revision_number",
            "created_at",
        ]


class CommitmentOfTradersObservationSerializer(serializers.ModelSerializer):
    """Serializer for CFTC Commitment of Traders institutional positioning."""

    commodity_code = serializers.CharField(source="commodity.code", read_only=True)
    commodity_name = serializers.CharField(source="commodity.name", read_only=True)
    endpoint_code = serializers.CharField(source="source_endpoint.code", read_only=True, default=None)
    money_manager_net = serializers.IntegerField(read_only=True)
    commercial_net = serializers.IntegerField(read_only=True)
    money_manager_net_pct_oi = serializers.FloatField(read_only=True)
    commercial_net_pct_oi = serializers.FloatField(read_only=True)

    class Meta:
        model = CommitmentOfTradersObservation
        fields = [
            "id",
            "commodity_code",
            "commodity_name",
            "observation_date",
            "report_type",
            "open_interest",
            "prod_merc_long",
            "prod_merc_short",
            "swap_long",
            "swap_short",
            "swap_spread",
            "money_manager_long",
            "money_manager_short",
            "money_manager_spread",
            "other_rept_long",
            "other_rept_short",
            "non_rept_long",
            "non_rept_short",
            "money_manager_net",
            "commercial_net",
            "money_manager_net_pct_oi",
            "commercial_net_pct_oi",
            "quality_status",
            "endpoint_code",
            "publication_time",
            "availability_time",
            "created_at",
        ]


class ObservationSummarySerializer(serializers.Serializer):
    """Statistical overview of market data observation store."""

    total_price_observations = serializers.IntegerField()
    total_prompt_observations = serializers.IntegerField()
    total_fundamental_observations = serializers.IntegerField()
    total_cot_observations = serializers.IntegerField()
    covered_commodities_count = serializers.IntegerField()
    covered_variables_count = serializers.IntegerField()
    latest_price_date = serializers.DateField(allow_null=True)
    latest_fundamental_date = serializers.DateField(allow_null=True)
    latest_cot_date = serializers.DateField(allow_null=True)
