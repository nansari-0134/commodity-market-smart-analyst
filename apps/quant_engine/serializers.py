"""
REST API Serializers for Quantitative Engine.
"""
from rest_framework import serializers
from apps.quant_engine.models import DiscoveryRegistry, EvidencePackageSnapshot


class DiscoveryRegistrySerializer(serializers.ModelSerializer):
    """Serializer for validated quantitative discoveries."""
    commodity_code = serializers.CharField(source="commodity.code", read_only=True)
    commodity_name = serializers.CharField(source="commodity.name", read_only=True)
    related_commodity_code = serializers.CharField(source="related_commodity.code", read_only=True, default=None)

    class Meta:
        model = DiscoveryRegistry
        fields = [
            "id",
            "discovery_type",
            "title",
            "commodity_code",
            "commodity_name",
            "related_commodity_code",
            "as_of_date",
            "confidence_score",
            "is_statistically_significant",
            "p_value",
            "t_statistic",
            "sample_size",
            "lookback_window",
            "evidence_payload",
            "is_active",
            "notes",
            "created_at",
        ]


class EvidencePackageSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for immutable evidence package snapshots."""
    commodity_code = serializers.CharField(source="commodity.code", read_only=True)

    class Meta:
        model = EvidencePackageSnapshot
        fields = [
            "id",
            "commodity_code",
            "as_of_date",
            "engine_version",
            "package_payload",
            "created_at",
        ]
