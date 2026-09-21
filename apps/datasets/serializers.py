"""
REST API Serializers for Dataset Master Catalog.
"""

from rest_framework import serializers
from apps.datasets.models import DatasetMaster


class CoveredCommoditySerializer(serializers.Serializer):
    """Compact representation of a commodity linked to a dataset."""

    code = serializers.CharField()
    name = serializers.CharField()
    sector = serializers.CharField()


class DatasetMasterListSerializer(serializers.ModelSerializer):
    """Compact serializer for listing canonical datasets."""

    domain_code = serializers.CharField(source="domain.code", read_only=True)
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    frequency_code = serializers.CharField(source="frequency.code", read_only=True)
    frequency_name = serializers.CharField(source="frequency.name", read_only=True)
    exchange_code = serializers.CharField(source="exchange.code", read_only=True, default=None)
    primary_commodity_code = serializers.CharField(source="primary_commodity.code", read_only=True, default=None)
    commodities_count = serializers.IntegerField(source="commodities.count", read_only=True)

    class Meta:
        model = DatasetMaster
        fields = [
            "id",
            "code",
            "name",
            "domain_code",
            "domain_name",
            "primary_commodity_code",
            "commodities_count",
            "exchange_code",
            "frequency_code",
            "frequency_name",
            "data_category",
            "update_cadence",
            "ingestion_mode",
            "license_type",
            "point_in_time_enabled",
            "supports_revisions",
            "sla_max_delay_minutes",
            "source_authority",
            "is_active",
            "display_order",
        ]


class DatasetMasterDetailSerializer(DatasetMasterListSerializer):
    """Detailed serializer including description, release timing schedule, and covered commodities."""

    covered_commodities = serializers.SerializerMethodField()

    class Meta(DatasetMasterListSerializer.Meta):
        fields = DatasetMasterListSerializer.Meta.fields + [
            "description",
            "release_schedule",
            "retention_policy",
            "documentation_url",
            "covered_commodities",
            "created_at",
            "updated_at",
        ]

    def get_covered_commodities(self, obj):
        return [
            {"code": c.code, "name": c.name, "sector": c.sector}
            for c in obj.commodities.all()
        ]


class DatasetSummarySerializer(serializers.Serializer):
    """Statistical summary of dataset catalog telemetry."""

    total_datasets = serializers.IntegerField()
    active_datasets = serializers.IntegerField()
    category_breakdown = serializers.DictField()
    cadence_breakdown = serializers.DictField()
    ingestion_mode_breakdown = serializers.DictField()
    license_breakdown = serializers.DictField()
    domain_breakdown = serializers.DictField()
