"""
REST API Views for metadata taxonomy endpoints.
"""
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from .models import DataDomainMaster, UnitMaster, FrequencyMaster
from .serializers import (
    DataDomainMasterSerializer,
    UnitMasterSerializer,
    FrequencyMasterSerializer,
)


class DataDomainListAPIView(ListAPIView):
    """
    Lists data domains. If ?top=true is specified, only returns root domains
    with their nested subdomains.
    """
    serializer_class = DataDomainMasterSerializer

    def get_queryset(self):
        qs = DataDomainMaster.objects.filter(is_active=True).prefetch_related("subdomains")
        category = self.request.query_params.get("category")
        top_only = self.request.query_params.get("top", "").lower() in ("true", "1")

        if category:
            qs = qs.filter(category=category.upper())
        if top_only:
            qs = qs.filter(parent__isnull=True)
        return qs.order_by("category", "display_order", "name")


class UnitListAPIView(ListAPIView):
    """Lists supported units of measure with optional type filter (?type=VOLUME)."""
    serializer_class = UnitMasterSerializer

    def get_queryset(self):
        qs = UnitMaster.objects.filter(is_active=True).select_related("base_unit")
        unit_type = self.request.query_params.get("type")
        if unit_type:
            qs = qs.filter(unit_type=unit_type.upper())
        return qs.order_by("unit_type", "code")


class FrequencyListAPIView(ListAPIView):
    """Lists observation frequencies."""
    serializer_class = FrequencyMasterSerializer

    def get_queryset(self):
        return FrequencyMaster.objects.filter(is_active=True).order_by("standard_interval_seconds", "name")


class MetadataSummaryAPIView(APIView):
    """
    Overview diagnostic endpoint providing counts across all canonical taxonomies.
    """
    def get(self, request):
        data = {
            "phase": "Phase 2: Metadata Schema",
            "data_domains": {
                "total": DataDomainMaster.objects.count(),
                "top_level": DataDomainMaster.objects.filter(parent__isnull=True).count(),
                "subdomains": DataDomainMaster.objects.filter(parent__isnull=False).count(),
            },
            "units_of_measure": {
                "total": UnitMaster.objects.count(),
                "base_units": UnitMaster.objects.filter(base_unit=models.F("id")).count() if hasattr(models, 'F') else None,
            },
            "frequencies": {
                "total": FrequencyMaster.objects.count(),
                "regular": FrequencyMaster.objects.filter(is_regular=True).count(),
                "irregular_event": FrequencyMaster.objects.filter(is_regular=False).count(),
            },
        }
        return Response(data, status=status.HTTP_200_OK)
