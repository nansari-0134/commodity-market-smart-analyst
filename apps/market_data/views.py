"""
REST API Views for Market Data & Time-Series Observations.
"""

import logging
from datetime import datetime, timezone, timedelta, date
from uuid import UUID
from django.core.cache import cache
from django.db.models import Max, Min, Count
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

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

        commodity = self.request.query_params.get("commodity")
        if commodity:
            try:
                c_uuid = UUID(commodity)
                qs = qs.filter(variable__commodity_id=c_uuid)
            except ValueError:
                qs = qs.filter(variable__commodity__code__iexact=commodity)

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


class CommitmentOfTradersAnalyticsAPIView(APIView):
    """
    Quantitative COT historical positioning analytics & seasonality engine.
    Returns:
    - full point-in-time time series (speculators, commercial hedgers, non-reportables, open interest)
    - weekly (W1-W53) and monthly (M1-M12) seasonality distributions and empirical averages
    - statistical summary, crowding percentile regimes, and year breakdown.
    """

    def get(self, request, *args, **kwargs):
        commodity_param = request.query_params.get("commodity", "CL").strip().upper()
        commodity = CommodityMaster.objects.filter(code=commodity_param).first()
        if not commodity:
            return Response(
                {"error": f"Commodity '{commodity_param}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        qs = (
            CommitmentOfTradersObservation.objects.filter(commodity=commodity)
            .order_by("observation_date")
            .values(
                "observation_date",
                "open_interest",
                "money_manager_long",
                "money_manager_short",
                "prod_merc_long",
                "prod_merc_short",
                "swap_long",
                "swap_short",
                "non_rept_long",
                "non_rept_short",
                "publication_time",
            )
        )

        time_series = []
        wk_acc: dict[int, list] = {}
        mo_acc: dict[int, list] = {}
        all_years = set()

        for row in qs:
            obs_date = row["observation_date"]
            yr = obs_date.year
            all_years.add(yr)
            wk = obs_date.isocalendar()[1]
            mo = obs_date.month

            oi = row["open_interest"] or 0
            nc_long = row["money_manager_long"] or 0
            nc_short = row["money_manager_short"] or 0
            nc_net = nc_long - nc_short

            cm_long = (row["prod_merc_long"] or 0) + (row["swap_long"] or 0)
            cm_short = (row["prod_merc_short"] or 0) + (row["swap_short"] or 0)
            cm_net = cm_long - cm_short

            nr_long = row["non_rept_long"] or 0
            nr_short = row["non_rept_short"] or 0
            nr_net = nr_long - nr_short

            nc_pct_oi = round((nc_net / oi) * 100, 2) if oi > 0 else 0.0
            cm_pct_oi = round((cm_net / oi) * 100, 2) if oi > 0 else 0.0

            item = {
                "date": obs_date.isoformat(),
                "year": yr,
                "week": wk,
                "month": mo,
                "open_interest": oi,
                "noncomm_long": nc_long,
                "noncomm_short": nc_short,
                "noncomm_net": nc_net,
                "comm_long": cm_long,
                "comm_short": cm_short,
                "comm_net": cm_net,
                "nonrept_long": nr_long,
                "nonrept_short": nr_short,
                "nonrept_net": nr_net,
                "noncomm_net_pct_oi": nc_pct_oi,
                "comm_net_pct_oi": cm_pct_oi,
            }
            time_series.append(item)

            wk_acc.setdefault(wk, []).append((nc_net, cm_net, nr_net, oi))
            mo_acc.setdefault(mo, []).append((nc_net, cm_net, nr_net, oi))

        def calc_avgs(acc):
            res = {}
            for key, vals in sorted(acc.items()):
                cnt = len(vals)
                res[key] = {
                    "avg_noncomm_net": round(sum(v[0] for v in vals) / cnt),
                    "avg_comm_net": round(sum(v[1] for v in vals) / cnt),
                    "avg_nonrept_net": round(sum(v[2] for v in vals) / cnt),
                    "avg_open_interest": round(sum(v[3] for v in vals) / cnt),
                    "count": cnt,
                }
            return res

        latest = time_series[-1] if time_series else None
        crowd_regime = "NEUTRAL"
        if latest:
            pct = latest["noncomm_net_pct_oi"]
            if pct >= 20.0:
                crowd_regime = "EXTREME_LONG"
            elif pct >= 10.0:
                crowd_regime = "MODERATE_LONG"
            elif pct <= -20.0:
                crowd_regime = "EXTREME_SHORT"
            elif pct <= -10.0:
                crowd_regime = "MODERATE_SHORT"

        return Response({
            "status": "ok",
            "commodity_code": commodity.code,
            "commodity_name": commodity.name,
            "total_observations": len(time_series),
            "historical_years": sorted(list(all_years)),
            "latest": {
                **(latest or {}),
                "crowding_regime": crowd_regime,
            },
            "time_series": time_series,
            "seasonality_weekly": calc_avgs(wk_acc),
            "seasonality_monthly": calc_avgs(mo_acc),
        })


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

        cache_key = f"live_quote_sync_{commodity.code}"
        last_check = cache.get(cache_key)

        latest_obs = (
            MarketPriceObservation.objects.filter(commodity=commodity, is_prompt=True)
            .order_by("-observation_date")
            .first()
        )
        is_stale = latest_obs is None or (date.today() - latest_obs.observation_date).days > 0

        if refresh or (is_stale and last_check is None):
            cache.set(cache_key, datetime.now(timezone.utc).timestamp(), timeout=120)
            try:
                from apps.market_data.providers.yahoo_finance import YahooMarketDataProvider
                provider = YahooMarketDataProvider()
                raw_obs = provider.fetch_price_observations(symbol=commodity.code, days=5)
                for raw in raw_obs:
                    MarketPriceObservation.objects.update_or_create(
                        commodity=commodity,
                        observation_date=raw.observation_date,
                        delivery_month="PROMPT",
                        revision_number=0,
                        defaults={
                            "is_prompt": True,
                            "open_price": raw.open_price,
                            "high_price": raw.high_price,
                            "low_price": raw.low_price,
                            "close_price": raw.close_price,
                            "settlement_price": raw.settlement_price,
                            "volume": raw.volume,
                            "publication_time": raw.publication_time,
                        },
                    )
            except Exception as exc:
                logger.warning(f"Live market data refresh failed for {commodity.code}: {exc}")

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
