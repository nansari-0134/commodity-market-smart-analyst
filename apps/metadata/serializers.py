"""
Serializers for Metadata Catalog API endpoints.
"""
from rest_framework import serializers
from .models import DataDomainMaster, UnitMaster, FrequencyMaster


class DataDomainSubdomainSerializer(serializers.ModelSerializer):
    """Serializer for child subdomains in tree view."""
    class Meta:
        model = DataDomainMaster
        fields = ("id", "code", "name", "category", "description", "display_order", "is_active")


class DataDomainMasterSerializer(serializers.ModelSerializer):
    """Serializer for primary data domains with nested subdomains."""
    subdomains = DataDomainSubdomainSerializer(many=True, read_only=True)
    hierarchy_path = serializers.ReadOnlyField()

    class Meta:
        model = DataDomainMaster
        fields = (
            "id",
            "code",
            "name",
            "category",
            "parent",
            "hierarchy_path",
            "description",
            "display_order",
            "is_active",
            "subdomains",
        )


class UnitMasterSerializer(serializers.ModelSerializer):
    """Serializer for Units of Measure."""
    base_unit_code = serializers.CharField(source="base_unit.code", read_only=True)

    class Meta:
        model = UnitMaster
        fields = (
            "id",
            "code",
            "name",
            "symbol",
            "unit_type",
            "base_unit",
            "base_unit_code",
            "conversion_factor",
            "description",
            "is_active",
        )


class FrequencyMasterSerializer(serializers.ModelSerializer):
    """Serializer for Observation Frequencies."""
    class Meta:
        model = FrequencyMaster
        fields = (
            "id",
            "code",
            "name",
            "standard_interval_seconds",
            "is_regular",
            "description",
            "is_active",
        )
