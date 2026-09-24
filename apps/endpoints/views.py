"""
REST API Views for Endpoint Master Catalog.
"""

from uuid import UUID
from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.endpoints.models import EndpointMaster
from apps.endpoints.serializers import (
    EndpointDetailSerializer,
    EndpointListSerializer,
    EndpointSummarySerializer,
)


class EndpointListAPIView(generics.ListAPIView):
    """
    List all registered data endpoints and route templates.

    Supported Filters:
    - `provider`: Filter by provider code or UUID
    - `dataset`: Filter by dataset code or UUID
    - `protocol`: Filter by transport protocol (REST_HTTP, FTP_SFTP, WEBSOCKET)
    - `http_method`: Filter by HTTP method (GET, POST)
    - `response_format`: Filter by payload format (JSON, CSV, TSV, XML, ZIP, PARQUET, EXCEL_XLSX)
    - `is_active`: Filter by active status (true/false)
    - `is_deprecated`: Filter by deprecation status (true/false)
    - `search`: Fuzzy search across code, name, path_template, and description
    """

    serializer_class = EndpointListSerializer

    def get_queryset(self):
        qs = EndpointMaster.objects.select_related("provider", "dataset").all()

        provider = self.request.query_params.get("provider")
        if provider:
            try:
                p_uuid = UUID(provider)
                qs = qs.filter(provider_id=p_uuid)
            except ValueError:
                qs = qs.filter(provider__code__iexact=provider)

        dataset = self.request.query_params.get("dataset")
        if dataset:
            try:
                d_uuid = UUID(dataset)
                qs = qs.filter(dataset_id=d_uuid)
            except ValueError:
                qs = qs.filter(dataset__code__iexact=dataset)

        protocol = self.request.query_params.get("protocol")
        if protocol:
            qs = qs.filter(protocol=protocol.upper())

        http_method = self.request.query_params.get("http_method")
        if http_method:
            qs = qs.filter(http_method=http_method.upper())

        response_format = self.request.query_params.get("response_format")
        if response_format:
            qs = qs.filter(response_format=response_format.upper())

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        is_deprecated = self.request.query_params.get("is_deprecated")
        if is_deprecated is not None:
            qs = qs.filter(is_deprecated=is_deprecated.lower() == "true")

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(path_template__icontains=search)
                | Q(description__icontains=search)
            )

        return qs


class EndpointDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve full specification of a single endpoint by canonical code or UUID.
    """

    serializer_class = EndpointDetailSerializer
    queryset = EndpointMaster.objects.select_related("provider", "dataset").all()

    def get_object(self):
        lookup = self.kwargs["code_or_uuid"]
        try:
            val = UUID(lookup)
            return generics.get_object_or_404(self.get_queryset(), id=val)
        except ValueError:
            return generics.get_object_or_404(self.get_queryset(), code__iexact=lookup)


class EndpointSummaryAPIView(APIView):
    """
    Statistical telemetry and aggregate breakdown of registered API endpoints.
    """

    def get(self, request, *args, **kwargs):
        total = EndpointMaster.objects.count()
        active = EndpointMaster.objects.filter(is_active=True).count()

        by_proto_qs = (
            EndpointMaster.objects.values("protocol")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        by_protocol = {item["protocol"]: item["count"] for item in by_proto_qs}

        by_method_qs = (
            EndpointMaster.objects.values("http_method")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        by_http_method = {item["http_method"]: item["count"] for item in by_method_qs}

        by_format_qs = (
            EndpointMaster.objects.values("response_format")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        by_response_format = {item["response_format"]: item["count"] for item in by_format_qs}

        by_prov_qs = (
            EndpointMaster.objects.values("provider__code")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        by_provider = {item["provider__code"]: item["count"] for item in by_prov_qs if item["provider__code"]}

        payload = {
            "total_endpoints": total,
            "active_endpoints": active,
            "by_protocol": by_protocol,
            "by_http_method": by_http_method,
            "by_response_format": by_response_format,
            "by_provider": by_provider,
        }

        serializer = EndpointSummarySerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)
