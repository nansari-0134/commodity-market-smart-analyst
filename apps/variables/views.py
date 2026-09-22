"""
REST API Views for Variable Master Catalog.
"""

from collections import Counter
import uuid
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.variables.models import VariableMaster
from apps.variables.serializers import (
    VariableMasterDetailSerializer,
    VariableMasterListSerializer,
    VariableSummarySerializer,
)


class VariableMasterListView(generics.ListAPIView):
    """
    List standardized commodity variables and metrics with rich query filters.

    Filter Query Parameters:
    - ?dataset=EIA_WPSR_PETROLEUM_STOCKS
    - ?commodity=CL | CORN | GOLD
    - ?domain=INVENTORIES | SUPPLY_DEMAND_BALANCES | CFTC_COT
    - ?unit=MBBL | BU | MT | PERCENT
    - ?data_type=DECIMAL | INTEGER
    - ?aggregation_method=LAST | SUM | AVG
    - ?is_benchmark=true | false
    - ?search=cushing | stocks | production
    """

    serializer_class = VariableMasterListSerializer

    def get_queryset(self):
        qs = VariableMaster.objects.select_related(
            "dataset", "domain", "commodity", "unit"
        ).filter(is_active=True)

        dataset = self.request.query_params.get("dataset")
        if dataset:
            qs = qs.filter(dataset__code__iexact=dataset)

        commodity = self.request.query_params.get("commodity")
        if commodity:
            qs = qs.filter(commodity__code__iexact=commodity)

        domain = self.request.query_params.get("domain")
        if domain:
            qs = qs.filter(domain__code__iexact=domain)

        unit = self.request.query_params.get("unit")
        if unit:
            qs = qs.filter(unit__code__iexact=unit)

        data_type = self.request.query_params.get("data_type")
        if data_type:
            qs = qs.filter(data_type__iexact=data_type)

        agg_method = self.request.query_params.get("aggregation_method")
        if agg_method:
            qs = qs.filter(aggregation_method__iexact=agg_method)

        is_benchmark = self.request.query_params.get("is_benchmark")
        if is_benchmark is not None:
            val = is_benchmark.lower() in ("true", "1", "yes")
            qs = qs.filter(is_benchmark=val)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(description__icontains=search)
            )

        return qs.order_by("display_order", "code")


class VariableMasterDetailView(generics.RetrieveAPIView):
    """
    Retrieve single variable specification details.
    Lookup by unique code (e.g. 'CRUDE_CUSHING_STOCKS') or UUID.
    """

    serializer_class = VariableMasterDetailSerializer

    def get_object(self):
        lookup = self.kwargs["lookup"]
        qs = VariableMaster.objects.select_related(
            "dataset", "domain", "commodity", "unit"
        )

        try:
            val = uuid.UUID(lookup)
            return get_object_or_404(qs, id=val)
        except ValueError:
            return get_object_or_404(qs, code__iexact=lookup)


class VariableSummaryView(APIView):
    """
    Return high-level distribution metrics for the Variable Master catalog.
    """

    def get(self, request, *args, **kwargs):
        qs = VariableMaster.objects.select_related("dataset", "domain")

        total_vars = qs.count()
        active_vars = qs.filter(is_active=True).count()
        benchmark_vars = qs.filter(is_benchmark=True).count()

        by_data_type = dict(Counter(qs.values_list("data_type", flat=True)))
        by_aggregation = dict(Counter(qs.values_list("aggregation_method", flat=True)))
        by_domain = dict(Counter(qs.values_list("domain__code", flat=True)))
        by_dataset = dict(Counter(qs.values_list("dataset__code", flat=True)))

        payload = {
            "total_variables": total_vars,
            "active_variables": active_vars,
            "benchmark_variables": benchmark_vars,
            "by_data_type": by_data_type,
            "by_aggregation_method": by_aggregation,
            "by_domain": by_domain,
            "by_dataset": by_dataset,
        }

        serializer = VariableSummarySerializer(payload)
        return Response(serializer.data)
