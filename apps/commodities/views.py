"""
REST API Views for Commodity Master, Specifications, and Multi-Exchange Listings.
"""
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from apps.commodities.models import CommodityMaster, CommodityExchangeListing, CommoditySector, SettlementMethod
from apps.commodities.serializers import (
    CommodityMasterListSerializer,
    CommodityMasterDetailSerializer,
    NestedExchangeListingSerializer,
)


def get_commodity_by_identifier(identifier: str) -> CommodityMaster:
    """Look up commodity by canonical code or UUID."""
    qs = CommodityMaster.objects.select_related(
        "primary_exchange", "base_unit", "pricing_unit", "standard_lot_unit"
    ).prefetch_related("exchange_listings__exchange", "exchange_listings__contract_unit")

    # Try code match first (case-insensitive)
    commodity = qs.filter(code__iexact=identifier).first()
    if commodity:
        return commodity

    # Try UUID match
    return get_object_or_404(qs, id=identifier)


class CommodityListAPIView(ListAPIView):
    """
    List canonical commodities with multi-dimensional filtering.
    Query parameters:
    - ?sector=ENERGY|AGRICULTURE|METALS_BASE|METALS_PRECIOUS|LIVESTOCK|FREIGHT_BULK|ENVIRONMENTAL
    - ?group=CRUDE_OIL|GRAINS|SOFTS|PRECIOUS_METALS...
    - ?exchange=NYMEX|ICE_EU|COMEX|MCX|CBOT... (filters commodities listed on that exchange)
    - ?settlement=PHYSICAL|CASH
    - ?search=crude|gold|corn
    """
    serializer_class = CommodityMasterListSerializer

    def get_queryset(self):
        qs = CommodityMaster.objects.filter(is_active=True).select_related(
            "primary_exchange", "base_unit", "pricing_unit"
        ).prefetch_related("exchange_listings")

        sector = self.request.query_params.get("sector")
        group = self.request.query_params.get("group")
        exchange = self.request.query_params.get("exchange")
        settlement = self.request.query_params.get("settlement")
        search = self.request.query_params.get("search")

        if sector:
            qs = qs.filter(sector__iexact=sector)
        if group:
            qs = qs.filter(group__iexact=group)
        if exchange:
            qs = qs.filter(
                Q(primary_exchange__code__iexact=exchange) |
                Q(exchange_listings__exchange__code__iexact=exchange)
            ).distinct()
        if settlement:
            qs = qs.filter(settlement_method__iexact=settlement)
        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(deliverable_grade_standard__icontains=search) |
                Q(primary_delivery_hub__icontains=search)
            )

        return qs.order_by("sector", "display_order", "code")


class CommodityDetailAPIView(APIView):
    """
    Retrieve full commodity profile including deliverable grade chemistry,
    delivery hub infrastructure, crop seasonality, and all active exchange listings.
    Lookup by code (e.g. /api/commodities/CL/) or UUID.
    """

    def get(self, request, identifier):
        try:
            commodity = get_commodity_by_identifier(identifier)
        except Exception:
            return Response(
                {"detail": f"Commodity '{identifier}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CommodityMasterDetailSerializer(commodity)
        return Response(serializer.data)


class CommodityListingsAPIView(APIView):
    """
    Lists the active exchange listings for a specific commodity
    showing where it actively trades across global venues.
    """

    def get(self, request, identifier):
        try:
            commodity = get_commodity_by_identifier(identifier)
        except Exception:
            return Response(
                {"detail": f"Commodity '{identifier}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        listings = commodity.exchange_listings.filter(is_active=True).select_related(
            "exchange", "contract_unit"
        ).order_by("-is_primary_benchmark", "-typical_daily_volume")
        serializer = NestedExchangeListingSerializer(listings, many=True)
        return Response({
            "commodity_code": commodity.code,
            "commodity_name": commodity.name,
            "listing_count": listings.count(),
            "listings": serializer.data,
        })


class CommoditySummaryAPIView(APIView):
    """Statistical summary across sectors, settlement types, and venues."""

    def get(self, request):
        commodities = CommodityMaster.objects.filter(is_active=True)
        listings = CommodityExchangeListing.objects.filter(is_active=True)

        sector_counts = {}
        for sector_choice, sector_label in CommoditySector.choices:
            count = commodities.filter(sector=sector_choice).count()
            if count > 0:
                sector_counts[sector_choice] = {
                    "label": sector_label,
                    "count": count,
                }

        settlement_counts = {
            "PHYSICAL": commodities.filter(settlement_method=SettlementMethod.PHYSICAL).count(),
            "CASH": commodities.filter(settlement_method=SettlementMethod.CASH).count(),
        }

        # Venues hosting active listings
        venue_listings = (
            listings.values("exchange__code", "exchange__name", "exchange__country")
            .annotate(contract_count=Count("id"))
            .order_by("-contract_count")
        )

        return Response({
            "total_commodities": commodities.count(),
            "total_exchange_listings": listings.count(),
            "sectors": sector_counts,
            "settlement_methods": settlement_counts,
            "venues": list(venue_listings),
        })


class CommoditySectorsAPIView(APIView):
    """Lists supported commodity sectors and groups."""

    def get(self, request):
        sectors = []
        for s_code, s_label in CommoditySector.choices:
            groups = list(
                CommodityMaster.objects.filter(sector=s_code, is_active=True)
                .values_list("group", flat=True)
                .distinct()
            )
            sectors.append({
                "code": s_code,
                "label": s_label,
                "groups": sorted(groups),
                "count": CommodityMaster.objects.filter(sector=s_code, is_active=True).count(),
            })
        return Response({"sectors": sectors})
