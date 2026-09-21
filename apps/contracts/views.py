"""
REST API Views for Contract Specifications, Expiries, and Derivative Master Analytics.
"""

from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.contracts.models import (
    ContractSpecification,
    ContractExpiry,
    SettlementMethod,
    InstrumentType,
)
from apps.contracts.serializers import (
    ContractSpecificationListSerializer,
    ContractSpecificationDetailSerializer,
    ContractExpirySerializer,
    ContractSummarySerializer,
)


class ContractSpecificationListView(generics.ListAPIView):
    """
    List and filter canonical contract specifications.
    Supports filtering by commodity code, exchange code/MIC, instrument type, and settlement method.
    """

    serializer_class = ContractSpecificationListSerializer

    def get_queryset(self):
        qs = ContractSpecification.objects.select_related(
            "commodity", "exchange", "contract_unit", "price_quote_unit"
        ).prefetch_related("expiries")

        commodity = self.request.query_params.get("commodity")
        if commodity:
            qs = qs.filter(commodity__code__iexact=commodity)

        exchange = self.request.query_params.get("exchange")
        if exchange:
            qs = qs.filter(Q(exchange__code__iexact=exchange) | Q(exchange__mic__iexact=exchange))

        instrument_type = self.request.query_params.get("instrument_type")
        if instrument_type:
            qs = qs.filter(instrument_type__iexact=instrument_type)

        settlement = self.request.query_params.get("settlement_method")
        if settlement:
            qs = qs.filter(settlement_method__iexact=settlement)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(symbol_root__icontains=search)
                | Q(name__icontains=search)
                | Q(commodity__name__icontains=search)
            )

        return qs.order_by("display_order", "exchange__code", "symbol_root")


class ContractSpecificationDetailView(generics.RetrieveAPIView):
    """
    Retrieve contract specification details with full nested prompt delivery expiries.
    Lookup by UUID or ticker root (e.g. 'CL', 'B', 'ZC').
    """

    serializer_class = ContractSpecificationDetailSerializer

    def get_object(self):
        lookup = self.kwargs["lookup"]
        qs = ContractSpecification.objects.select_related(
            "commodity", "exchange", "contract_unit", "price_quote_unit"
        ).prefetch_related("expiries")

        # Check if UUID
        try:
            return qs.get(id=lookup)
        except (ValueError, ValidationError, ContractSpecification.DoesNotExist):
            pass

        # Check if exchange:symbol formatted (e.g. XNYM:CL)
        if ":" in lookup:
            mic, root = lookup.split(":", 1)
            return get_object_or_404(qs, exchange__mic__iexact=mic, symbol_root__iexact=root)

        # Lookup by unique symbol_root (or first if cross-listed)
        obj = qs.filter(symbol_root__iexact=lookup).first()
        if obj:
            return obj

        return get_object_or_404(qs, symbol_root__iexact=lookup)


class ContractExpiryListView(generics.ListAPIView):
    """
    List and filter forward contract delivery months.
    Supports filtering by root ticker, calendar year, month, month code, and expired status.
    """

    serializer_class = ContractExpirySerializer

    def get_queryset(self):
        qs = ContractExpiry.objects.select_related("specification__exchange", "specification__commodity")

        spec_symbol = self.request.query_params.get("specification") or self.request.query_params.get("symbol_root")
        if spec_symbol:
            qs = qs.filter(specification__symbol_root__iexact=spec_symbol)

        exchange = self.request.query_params.get("exchange")
        if exchange:
            qs = qs.filter(
                Q(specification__exchange__code__iexact=exchange)
                | Q(specification__exchange__mic__iexact=exchange)
            )

        year = self.request.query_params.get("year")
        if year:
            try:
                qs = qs.filter(contract_year=int(year))
            except ValueError:
                pass

        month = self.request.query_params.get("month")
        if month:
            try:
                qs = qs.filter(contract_month=int(month))
            except ValueError:
                pass

        month_code = self.request.query_params.get("month_code")
        if month_code:
            qs = qs.filter(contract_month_code__iexact=month_code)

        is_expired = self.request.query_params.get("is_expired")
        if is_expired is not None:
            val = is_expired.lower() in ["true", "1", "yes"]
            qs = qs.filter(is_expired=val)

        return qs.order_by("specification__symbol_root", "contract_year", "contract_month")


class ContractExpiryDetailView(generics.RetrieveAPIView):
    """
    Retrieve single delivery contract month details.
    Lookup by standardized contract ticker (e.g. 'CLZ26', 'BRENTF27', 'ZCH27') or UUID.
    """

    serializer_class = ContractExpirySerializer

    def get_object(self):
        lookup = self.kwargs["lookup"]
        qs = ContractExpiry.objects.select_related("specification__exchange", "specification__commodity")

        try:
            return qs.get(id=lookup)
        except (ValueError, ValidationError, ContractExpiry.DoesNotExist):
            pass

        return get_object_or_404(qs, contract_symbol__iexact=lookup)


class ContractSummaryView(APIView):
    """
    Statistical diagnostic summary of derivative specifications and prompt contract delivery cycles.
    """

    def get(self, request, *args, **kwargs):
        total_specs = ContractSpecification.objects.count()
        total_expiries = ContractExpiry.objects.count()
        active_expiries = ContractExpiry.objects.filter(is_expired=False).count()
        expired_contracts = total_expiries - active_expiries

        # Settlement breakdown
        settlement_counts = dict(
            ContractSpecification.objects.values_list("settlement_method").annotate(c=Count("id"))
        )

        # Instrument type breakdown
        instrument_counts = dict(
            ContractSpecification.objects.values_list("instrument_type").annotate(c=Count("id"))
        )

        # Exchange breakdown
        exchange_counts = dict(
            ContractSpecification.objects.values_list("exchange__code").annotate(c=Count("id"))
        )

        data = {
            "total_specifications": total_specs,
            "total_expiries": total_expiries,
            "active_expiries": active_expiries,
            "expired_contracts": expired_contracts,
            "settlement_method_breakdown": settlement_counts,
            "instrument_type_breakdown": instrument_counts,
            "exchange_breakdown": exchange_counts,
        }

        serializer = ContractSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
