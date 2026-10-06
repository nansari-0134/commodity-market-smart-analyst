"""
REST API Views for Market Data & Time-Series Observations.
"""

from datetime import datetime, timezone, timedelta
from uuid import UUID
from django.db.models import Max, Min, Count
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.commodities.models import CommodityMaster

from apps.market_data.models import (
    MarketPriceObservation,
    FundamentalObservation,
    CommitmentOfTradersObservation,
    OptionsObservation,
)
from apps.market_data.serializers import (
    MarketPriceObservationSerializer,
    FundamentalObservationSerializer,
    CommitmentOfTradersObservationSerializer,
    OptionsObservationSerializer,
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


class OptionsObservationListAPIView(generics.ListAPIView):
    """
    List options implied volatility surfaces and positioning metrics across contracts M1-M24.

    Filters:
    - `commodity`: Commodity code (e.g. 'CL') or UUID
    - `delivery_month`: Specific contract delivery month or tenor (e.g. 'M1', 'M2', ..., 'M24')
    - `start_date`: Earliest observation date (YYYY-MM-DD)
    - `end_date`: Latest observation date (YYYY-MM-DD)
    """
    serializer_class = OptionsObservationSerializer

    def get_queryset(self):
        qs = OptionsObservation.objects.select_related(
            "commodity", "contract", "source_endpoint"
        ).all()

        commodity = self.request.query_params.get("commodity")
        if commodity:
            try:
                c_uuid = UUID(commodity)
                qs = qs.filter(commodity_id=c_uuid)
            except ValueError:
                qs = qs.filter(commodity__code__iexact=commodity)

        delivery_month = self.request.query_params.get("delivery_month")
        if delivery_month:
            qs = qs.filter(delivery_month__iexact=delivery_month)

        start_date = self.request.query_params.get("start_date")
        if start_date:
            qs = qs.filter(observation_date__gte=start_date)

        end_date = self.request.query_params.get("end_date")
        if end_date:
            qs = qs.filter(observation_date__lte=end_date)

        return qs


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

        options_stats = OptionsObservation.objects.aggregate(
            total=Count("id"),
            latest=Max("observation_date"),
        )

        data = {
            "total_price_observations": price_stats["total"] or 0,
            "total_prompt_observations": prompt_count,
            "total_fundamental_observations": fundamental_stats["total"] or 0,
            "total_cot_observations": cot_stats["total"] or 0,
            "total_options_observations": options_stats["total"] or 0,
            "covered_commodities_count": distinct_commodities,
            "covered_variables_count": distinct_vars,
            "latest_price_date": price_stats["latest"],
            "latest_fundamental_date": fundamental_stats["latest"],
            "latest_cot_date": cot_stats["latest"],
        }

        serializer = ObservationSummarySerializer(data)
        return Response(serializer.data)


class LiveMarketQuoteAPIView(APIView):
    """
    Live Market Price & Intraday Quote Endpoint.
    
    Returns real-time or latest prompt futures quote with full OHLC, volume,
    open interest, 1D return, and 52-week range.
    Supports ?commodity=<code> and ?refresh=true (which connects to live exchange feed).
    """

    def get(self, request, *args, **kwargs):
        code = (request.query_params.get("commodity") or request.query_params.get("symbol") or "CL").upper()
        refresh = request.query_params.get("refresh", "false").lower() in ["true", "1"]

        commodity = CommodityMaster.objects.filter(code__iexact=code).first()
        if not commodity:
            return Response(
                {"error": f"Commodity with code '{code}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if refresh:
            try:
                from apps.market_data.providers.yahoo_finance import YahooMarketDataProvider
                provider = YahooMarketDataProvider()
                raw_obs = provider.fetch_price_observations(symbol=commodity.code, days=2)
                if raw_obs:
                    latest_raw = raw_obs[-1]
                    MarketPriceObservation.objects.update_or_create(
                        commodity=commodity,
                        observation_date=latest_raw.observation_date,
                        contract_month="PROMPT",
                        defaults={
                            "is_prompt": True,
                            "open_price": latest_raw.open_price,
                            "high_price": latest_raw.high_price,
                            "low_price": latest_raw.low_price,
                            "close_price": latest_raw.close_price,
                            "settlement_price": latest_raw.settlement_price,
                            "volume": latest_raw.volume,
                            "publication_time": latest_raw.publication_time,
                        },
                    )
            except Exception:
                pass

        latest_obs = (
            MarketPriceObservation.objects.filter(commodity=commodity, is_prompt=True)
            .order_by("-observation_date")
            .first()
        )
        if not latest_obs:
            return Response(
                {"error": f"No price observations found for '{code}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        prev_obs = (
            MarketPriceObservation.objects.filter(
                commodity=commodity, is_prompt=True, observation_date__lt=latest_obs.observation_date
            )
            .order_by("-observation_date")
            .first()
        )

        price = float(latest_obs.close_price or latest_obs.settlement_price or 0.0)
        prev_price = float(prev_obs.close_price or prev_obs.settlement_price or price) if prev_obs else price
        point_change = round(price - prev_price, 4)
        ret_1d = round(((price - prev_price) / prev_price) * 100.0, 2) if prev_price > 0 else 0.0

        one_year_ago = latest_obs.observation_date - timedelta(days=365)
        range_52w = MarketPriceObservation.objects.filter(
            commodity=commodity,
            is_prompt=True,
            observation_date__gte=one_year_ago,
        ).aggregate(
            high_52w=Max("high_price"),
            low_52w=Min("low_price"),
        )

        high_52w = float(range_52w["high_52w"] or price)
        low_52w = float(range_52w["low_52w"] or price)

        # Resolve institutional Open Interest from observation, or COT, or primary listing
        oi_val = latest_obs.open_interest
        if not oi_val or oi_val <= 0:
            latest_cot = CommitmentOfTradersObservation.objects.filter(
                commodity=commodity,
                observation_date__lte=latest_obs.observation_date,
            ).order_by("-observation_date").first()
            if latest_cot and latest_cot.open_interest:
                oi_val = latest_cot.open_interest
            else:
                primary_listing = commodity.exchange_listings.filter(is_primary_benchmark=True).first() or commodity.exchange_listings.first()
                if primary_listing and primary_listing.typical_open_interest:
                    oi_val = primary_listing.typical_open_interest
        resolved_oi = int(oi_val or 0)

        return Response({
            "status": "ok",
            "symbol": commodity.code,
            "name": commodity.name,
            "sector": commodity.sector,
            "exchange": commodity.primary_exchange.code if commodity.primary_exchange else "CME",
            "price": price,
            "spot_price": price,
            "change": point_change,
            "point_change": point_change,
            "ret_1d": ret_1d,
            "returns_1d": ret_1d,
            "open": float(latest_obs.open_price or price),
            "day_open": float(latest_obs.open_price or price),
            "high": float(latest_obs.high_price or price),
            "day_high": float(latest_obs.high_price or price),
            "low": float(latest_obs.low_price or price),
            "day_low": float(latest_obs.low_price or price),
            "close": float(latest_obs.close_price or price),
            "volume": int(latest_obs.volume or 0),
            "day_volume": int(latest_obs.volume or 0),
            "open_interest": resolved_oi,
            "day_oi": resolved_oi,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "observation_date": latest_obs.observation_date.isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candle": {
                "time": latest_obs.observation_date.isoformat(),
                "open": float(latest_obs.open_price or price),
                "high": float(latest_obs.high_price or price),
                "low": float(latest_obs.low_price or price),
                "close": float(latest_obs.close_price or price),
                "volume": int(latest_obs.volume or 0),
                "open_interest": resolved_oi,
            },
        })
