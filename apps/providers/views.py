"""
REST API Views for Provider Master Catalog.
"""

from uuid import UUID
from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.providers.models import ProviderMaster
from apps.providers.serializers import (
    ProviderDetailSerializer,
    ProviderListSerializer,
    ProviderSummarySerializer,
)


class ProviderListAPIView(generics.ListAPIView):
    """
    List all registered data providers and calculation engines.

    Supported Filters:
    - `provider_type`: Filter by provider category (e.g. 'GOVERNMENT_PUBLIC', 'EXCHANGE_DIRECT')
    - `auth_type`: Filter by authentication protocol (e.g. 'NONE_PUBLIC', 'BEARER_TOKEN')
    - `is_active`: Filter by active status (true/false)
    - `has_rate_limit`: Filter by whether rate limits are defined (true/false)
    - `search`: Fuzzy search across code, name, and description
    """

    serializer_class = ProviderListSerializer

    def get_queryset(self):
        qs = ProviderMaster.objects.select_related("fallback_provider").all()

        provider_type = self.request.query_params.get("provider_type")
        if provider_type:
            qs = qs.filter(provider_type=provider_type.upper())

        auth_type = self.request.query_params.get("auth_type")
        if auth_type:
            qs = qs.filter(auth_type=auth_type.upper())

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        has_rate_limit = self.request.query_params.get("has_rate_limit")
        if has_rate_limit is not None:
            if has_rate_limit.lower() == "true":
                qs = qs.filter(rate_limit_requests__isnull=False)
            elif has_rate_limit.lower() == "false":
                qs = qs.filter(rate_limit_requests__isnull=True)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(description__icontains=search)
            )

        return qs


class ProviderDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve full specification of a single provider by canonical code or UUID.
    """

    serializer_class = ProviderDetailSerializer
    queryset = ProviderMaster.objects.select_related("fallback_provider").all()

    def get_object(self):
        lookup = self.kwargs["code_or_uuid"]
        try:
            val = UUID(lookup)
            return generics.get_object_or_404(self.get_queryset(), id=val)
        except ValueError:
            return generics.get_object_or_404(self.get_queryset(), code=lookup.upper())


class ProviderSummaryAPIView(APIView):
    """
    Statistical telemetry and aggregate breakdown of registered data providers.
    """

    def get(self, request, *args, **kwargs):
        total = ProviderMaster.objects.count()
        active = ProviderMaster.objects.filter(is_active=True).count()
        with_rate_limits = ProviderMaster.objects.filter(rate_limit_requests__isnull=False).count()
        with_fallbacks = ProviderMaster.objects.filter(fallback_provider__isnull=False).count()

        by_type_qs = (
            ProviderMaster.objects.values("provider_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        by_provider_type = {item["provider_type"]: item["count"] for item in by_type_qs}

        by_auth_qs = (
            ProviderMaster.objects.values("auth_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        by_auth_type = {item["auth_type"]: item["count"] for item in by_auth_qs}

        payload = {
            "total_providers": total,
            "active_providers": active,
            "with_rate_limits": with_rate_limits,
            "with_fallbacks": with_fallbacks,
            "by_provider_type": by_provider_type,
            "by_auth_type": by_auth_type,
        }

        serializer = ProviderSummarySerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)
