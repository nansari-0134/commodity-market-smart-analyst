"""
REST API Views for Market Data & Time-Series Observations.
"""

from uuid import UUID
from django.db.models import Max, Min, Count
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.market_data.models import (
    MarketPriceObservation,
    FundamentalObservation,
    CommitmentOfTradersObservation,
)
from apps.market_data.serializers import (
    MarketPriceObservationSerializer,
    FundamentalObservationSerializer,
    CommitmentOfTradersObservationSerializer,
    ObservationSummarySerializer,
)


class MarketPriceListAPIView(generics.ListAPIView):
    """
    List historical and intraday market price observations.

    Filters:
    - `commodity`: Commodity code (e.g. 'CL', 'BZ') or UUID
    - `is_prompt`: 'true' for benchmark front-month contracts only
    - `delivery_month`: Specific contract delivery month (e.g. '2026-11')
    - `start_date`: Earliest observation date (YYYY-MM-DD)
    - `end_date`: Latest observation date (YYYY-MM-DD)
    - `is_preliminary`: 'true' / 'false'
    """
    serializer_class = MarketPriceObservationSerializer

    def get_queryset(self):
        qs = MarketPriceObservation.objects.select_related(
            "commodity", "contract", "source_endpoint"
        ).all()

        commodity = self.request.query_params.get("commodity")
        if commodity:
            try:
                c_uuid = UUID(commodity)
                qs = qs.filter(commodity_id=c_uuid)
            except ValueError:
                qs = qs.filter(commodity__code__iexact=commodity)

        is_prompt = self.request.query_params.get("is_prompt")
        if is_prompt is not None:
            if is_prompt.lower() in ["true", "1"]:
                qs = qs.filter(is_prompt=True)
            elif is_prompt.lower() in ["false", "0"]:
                qs = qs.filter(is_prompt=False)

        delivery_month = self.request.query_params.get("delivery_month")
        if delivery_month:
            qs = qs.filter(delivery_month__iexact=delivery_month)

        start_date = self.request.query_params.get("start_date")
        if start_date:
            qs = qs.filter(observation_date__gte=start_date)

        end_date = self.request.query_params.get("end_date")
        if end_date:
            qs = qs.filter(observation_date__lte=end_date)

        is_preliminary = self.request.query_params.get("is_preliminary")
        if is_preliminary is not None:
            qs = qs.filter(is_preliminary=is_preliminary.lower() in ["true", "1"])

        return qs


class MarketPriceDetailAPIView(generics.RetrieveAPIView):
    """Retrieve an individual market price observation by UUID."""
    queryset = MarketPriceObservation.objects.select_related(
        "commodity", "contract", "source_endpoint"
    ).all()
    serializer_class = MarketPriceObservationSerializer


class FundamentalObservationListAPIView(generics.ListAPIView):
    """
    List fundamental supply-demand and inventory time series.

    Filters:
    - `variable`: Variable code (e.g. 'EIA_CRUDE_STOCKS_WEEKLY') or UUID
    - `start_date`: Earliest observation date (YYYY-MM-DD)
    - `end_date`: Latest observation date (YYYY-MM-DD)
    - `is_preliminary`: 'true' / 'false'
    """
    serializer_class = FundamentalObservationSerializer

    def get_queryset(self):
        qs = FundamentalObservation.objects.select_related(
            "variable", "unit", "source_endpoint"
        ).all()

        variable = self.request.query_params.get("variable")
        if variable:
            try:
                v_uuid = UUID(variable)
                qs = qs.filter(variable_id=v_uuid)
            except ValueError:
                qs = qs.filter(variable__code__iexact=variable)

        start_date = self.request.query_params.get("start_date")
        if start_date:
            qs = qs.filter(observation_date__gte=start_date)

        end_date = self.request.query_params.get("end_date")
        if end_date:
            qs = qs.filter(observation_date__lte=end_date)

        is_preliminary = self.request.query_params.get("is_preliminary")
        if is_preliminary is not None:
            qs = qs.filter(is_preliminary=is_preliminary.lower() in ["true", "1"])

        return qs


class FundamentalObservationDetailAPIView(generics.RetrieveAPIView):
    """Retrieve an individual fundamental observation by UUID."""
    queryset = FundamentalObservation.objects.select_related(
        "variable", "unit", "source_endpoint"
    ).all()
    serializer_class = FundamentalObservationSerializer


class CommitmentOfTradersListAPIView(generics.ListAPIView):
    """
    List CFTC Commitment of Traders (COT) institutional positioning records.

    Filters:
    - `commodity`: Commodity code (e.g. 'CL') or UUID
    - `report_type`: 'DISAGGREGATED', 'LEGACY', or 'FINANCIAL'
    - `start_date`: Earliest observation date (YYYY-MM-DD)
    - `end_date`: Latest observation date (YYYY-MM-DD)
    """
    serializer_class = CommitmentOfTradersObservationSerializer

    def get_queryset(self):
        qs = CommitmentOfTradersObservation.objects.select_related(
            "commodity", "source_endpoint"
        ).all()

        commodity = self.request.query_params.get("commodity")
        if commodity:
            try:
                c_uuid = UUID(commodity)
                qs = qs.filter(commodity_id=c_uuid)
            except ValueError:
                qs = qs.filter(commodity__code__iexact=commodity)

        report_type = self.request.query_params.get("report_type")
        if report_type:
            qs = qs.filter(report_type__iexact=report_type)

        start_date = self.request.query_params.get("start_date")
        if start_date:
            qs = qs.filter(observation_date__gte=start_date)

        end_date = self.request.query_params.get("end_date")
        if end_date:
            qs = qs.filter(observation_date__lte=end_date)

        return qs


class CommitmentOfTradersDetailAPIView(generics.RetrieveAPIView):
    """Retrieve an individual COT observation by UUID."""
    queryset = CommitmentOfTradersObservation.objects.select_related(
        "commodity", "source_endpoint"
    ).all()
    serializer_class = CommitmentOfTradersObservationSerializer


class MarketDataSummaryAPIView(APIView):
    """Statistical overview of market data observation store."""

    def get(self, request, *args, **kwargs):
        price_stats = MarketPriceObservation.objects.aggregate(
            total=Count("id"),
            latest=Max("observation_date"),
        )
        prompt_count = MarketPriceObservation.objects.filter(is_prompt=True).count()
        distinct_commodities = MarketPriceObservation.objects.values("commodity").distinct().count()

        fundamental_stats = FundamentalObservation.objects.aggregate(
            total=Count("id"),
            latest=Max("observation_date"),
        )
        distinct_vars = FundamentalObservation.objects.values("variable").distinct().count()

        cot_stats = CommitmentOfTradersObservation.objects.aggregate(
            total=Count("id"),
            latest=Max("observation_date"),
        )

        data = {
            "total_price_observations": price_stats["total"] or 0,
            "total_prompt_observations": prompt_count,
            "total_fundamental_observations": fundamental_stats["total"] or 0,
            "total_cot_observations": cot_stats["total"] or 0,
            "covered_commodities_count": distinct_commodities,
            "covered_variables_count": distinct_vars,
            "latest_price_date": price_stats["latest"],
            "latest_fundamental_date": fundamental_stats["latest"],
            "latest_cot_date": cot_stats["latest"],
        }

        serializer = ObservationSummarySerializer(data)
        return Response(serializer.data)
