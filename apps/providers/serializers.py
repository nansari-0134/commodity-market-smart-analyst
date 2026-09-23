"""
REST API Serializers for Provider Master Catalog.
"""

from rest_framework import serializers

from apps.providers.models import ProviderMaster


class ProviderListSerializer(serializers.ModelSerializer):
    """Compact serializer for listing external providers and data sources."""

    provider_type_display = serializers.CharField(source="get_provider_type_display", read_only=True)
    auth_type_display = serializers.CharField(source="get_auth_type_display", read_only=True)
    fallback_provider_code = serializers.CharField(source="fallback_provider.code", read_only=True, default=None)
    fallback_provider_name = serializers.CharField(source="fallback_provider.name", read_only=True, default=None)

    class Meta:
        model = ProviderMaster
        fields = [
            "id",
            "code",
            "name",
            "provider_type",
            "provider_type_display",
            "base_url",
            "auth_type",
            "auth_type_display",
            "env_var_name",
            "rate_limit_requests",
            "rate_limit_window_seconds",
            "target_sla_pct",
            "fallback_provider_code",
            "fallback_provider_name",
            "is_active",
            "display_order",
        ]


class ProviderDetailSerializer(ProviderListSerializer):
    """Detailed serializer including methodology notes, contacts, and audit timestamps."""

    class Meta(ProviderListSerializer.Meta):
        fields = ProviderListSerializer.Meta.fields + [
            "description",
            "documentation_url",
            "support_contact",
            "auth_param_name",
            "backoff_seconds",
            "notes",
            "created_at",
            "updated_at",
        ]


class ProviderSummarySerializer(serializers.Serializer):
    """Statistical summary of provider catalog telemetry."""

    total_providers = serializers.IntegerField()
    active_providers = serializers.IntegerField()
    with_rate_limits = serializers.IntegerField()
    with_fallbacks = serializers.IntegerField()
    by_provider_type = serializers.DictField()
    by_auth_type = serializers.DictField()
