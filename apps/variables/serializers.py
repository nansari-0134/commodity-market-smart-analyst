"""
REST API Serializers for Variable Master Catalog.
"""

from rest_framework import serializers

from apps.variables.models import VariableMaster


class VariableMasterListSerializer(serializers.ModelSerializer):
    """Compact serializer for listing canonical variables and metrics."""

    dataset_code = serializers.CharField(source="dataset.code", read_only=True)
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)
    domain_code = serializers.CharField(source="domain.code", read_only=True)
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    commodity_code = serializers.CharField(source="commodity.code", read_only=True, default=None)
    commodity_name = serializers.CharField(source="commodity.name", read_only=True, default=None)
    unit_code = serializers.CharField(source="unit.code", read_only=True)
    unit_name = serializers.CharField(source="unit.name", read_only=True)

    class Meta:
        model = VariableMaster
        fields = [
            "id",
            "code",
            "name",
            "dataset_code",
            "dataset_name",
            "domain_code",
            "domain_name",
            "commodity_code",
            "commodity_name",
            "unit_code",
            "unit_name",
            "data_type",
            "aggregation_method",
            "seasonal_adjustment",
            "default_transformation",
            "is_benchmark",
            "is_active",
            "display_order",
        ]


class VariableMasterDetailSerializer(VariableMasterListSerializer):
    """Detailed serializer including description and audit timestamps."""

    class Meta(VariableMasterListSerializer.Meta):
        fields = VariableMasterListSerializer.Meta.fields + [
            "description",
            "created_at",
            "updated_at",
        ]


class VariableSummarySerializer(serializers.Serializer):
    """Statistical summary of variable catalog telemetry."""

    total_variables = serializers.IntegerField()
    active_variables = serializers.IntegerField()
    benchmark_variables = serializers.IntegerField()
    by_data_type = serializers.DictField()
    by_aggregation_method = serializers.DictField()
    by_domain = serializers.DictField()
    by_dataset = serializers.DictField()
