"""
REST API Serializers for Endpoint Master Catalog.
"""

from rest_framework import serializers

from apps.endpoints.models import EndpointMaster


class EndpointListSerializer(serializers.ModelSerializer):
    """Compact serializer for listing and filtering API endpoints."""

    provider_code = serializers.CharField(source="provider.code", read_only=True)
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    dataset_code = serializers.CharField(source="dataset.code", read_only=True, default=None)
    dataset_name = serializers.CharField(source="dataset.name", read_only=True, default=None)
    protocol_display = serializers.CharField(source="get_protocol_display", read_only=True)
    response_format_display = serializers.CharField(source="get_response_format_display", read_only=True)
    full_url = serializers.CharField(source="get_full_url", read_only=True)

    class Meta:
        model = EndpointMaster
        fields = [
            "id",
            "code",
            "name",
            "provider_code",
            "provider_name",
            "dataset_code",
            "dataset_name",
            "protocol",
            "protocol_display",
            "http_method",
            "path_template",
            "full_url",
            "response_format",
            "response_format_display",
            "cache_ttl_seconds",
            "is_active",
            "is_deprecated",
        ]


class EndpointDetailSerializer(EndpointListSerializer):
    """Full detail serializer including query parameter schemas, envelope selectors, and audit timestamps."""

    class Meta(EndpointListSerializer.Meta):
        fields = EndpointListSerializer.Meta.fields + [
            "description",
            "data_envelope_path",
            "default_params",
            "custom_headers",
            "notes",
            "created_at",
            "updated_at",
        ]


class EndpointSummarySerializer(serializers.Serializer):
    """Statistical summary of endpoint catalog telemetry."""

    total_endpoints = serializers.IntegerField()
    active_endpoints = serializers.IntegerField()
    by_protocol = serializers.DictField(child=serializers.IntegerField())
    by_http_method = serializers.DictField(child=serializers.IntegerField())
    by_response_format = serializers.DictField(child=serializers.IntegerField())
    by_provider = serializers.DictField(child=serializers.IntegerField())
