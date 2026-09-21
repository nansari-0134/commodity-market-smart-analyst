"""
REST API Views for Dataset Master Catalog and Ingestion Analytics.
"""

from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.datasets.models import DatasetMaster
from apps.datasets.serializers import (
    DatasetMasterListSerializer,
    DatasetMasterDetailSerializer,
    DatasetSummarySerializer,
)


class DatasetMasterListView(generics.ListAPIView):
    """
    List and filter canonical dataset catalog entries.
    Supports filtering by domain, category, update cadence, ingestion mode, commodity, and venue.
    """

    serializer_class = DatasetMasterListSerializer

    def get_queryset(self):
        qs = DatasetMaster.objects.select_related(
            "domain", "frequency", "exchange", "primary_commodity"
        ).prefetch_related("commodities")

        domain = self.request.query_params.get("domain")
        if domain:
            qs = qs.filter(Q(domain__code__iexact=domain) | Q(domain__name__icontains=domain))

        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(data_category__iexact=category)

        cadence = self.request.query_params.get("cadence")
        if cadence:
            qs = qs.filter(update_cadence__iexact=cadence)

        ingestion_mode = self.request.query_params.get("ingestion_mode")
        if ingestion_mode:
            qs = qs.filter(ingestion_mode__iexact=ingestion_mode)

        license_type = self.request.query_params.get("license")
        if license_type:
            qs = qs.filter(license_type__iexact=license_type)

        commodity = self.request.query_params.get("commodity")
        if commodity:
            qs = qs.filter(
                Q(primary_commodity__code__iexact=commodity)
                | Q(commodities__code__iexact=commodity)
            ).distinct()

        exchange = self.request.query_params.get("exchange")
        if exchange:
            qs = qs.filter(Q(exchange__code__iexact=exchange) | Q(exchange__mic__iexact=exchange))

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(source_authority__icontains=search)
                | Q(description__icontains=search)
            )

        return qs.order_by("display_order", "code")


class DatasetMasterDetailView(generics.RetrieveAPIView):
    """
    Retrieve single dataset specification details.
    Lookup by unique code (e.g. 'CME_FUTURES_EOD', 'EIA_WPSR_PETROLEUM') or UUID.
    """

    serializer_class = DatasetMasterDetailSerializer

    def get_object(self):
        lookup = self.kwargs["lookup"]
        qs = DatasetMaster.objects.select_related(
            "domain", "frequency", "exchange", "primary_commodity"
        ).prefetch_related("commodities")

        try:
            return qs.get(id=lookup)
        except (ValueError, ValidationError, DatasetMaster.DoesNotExist):
            pass

        return get_object_or_404(qs, code__iexact=lookup)


class DatasetSummaryView(APIView):
    """
    Statistical diagnostics summary of cataloged datasets across domains, categories, and cadences.
    """

    def get(self, request, *args, **kwargs):
        total_datasets = DatasetMaster.objects.count()
        active_datasets = DatasetMaster.objects.filter(is_active=True).count()

        category_counts = dict(
            DatasetMaster.objects.values_list("data_category").annotate(c=Count("id"))
        )
        cadence_counts = dict(
            DatasetMaster.objects.values_list("update_cadence").annotate(c=Count("id"))
        )
        mode_counts = dict(
            DatasetMaster.objects.values_list("ingestion_mode").annotate(c=Count("id"))
        )
        license_counts = dict(
            DatasetMaster.objects.values_list("license_type").annotate(c=Count("id"))
        )
        domain_counts = dict(
            DatasetMaster.objects.values_list("domain__code").annotate(c=Count("id"))
        )

        data = {
            "total_datasets": total_datasets,
            "active_datasets": active_datasets,
            "category_breakdown": category_counts,
            "cadence_breakdown": cadence_counts,
            "ingestion_mode_breakdown": mode_counts,
            "license_breakdown": license_counts,
            "domain_breakdown": domain_counts,
        }

        serializer = DatasetSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
