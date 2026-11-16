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
import numpy as np

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


class ForwardCurveAnalyticsAPIView(APIView):
    """
    Quantitative Forward Curve & Options Volatility Surface Analytics.
    Returns:
    - 24-contract forward strip (M1 to M24) with settlement prices, spread to M1, annualized roll yield, and volume
    - Historical comparison curves: Current, 1-Week Ago, 1-Month Ago, 1-Year Ago
    - Options implied volatility strip (ATM IV, 25D delta skew, Put/Call volume and OI ratios)
    - Term structure slope, contango/backwardation classification, and roll yield summary.
    """
    def get(self, request, *args, **kwargs):
        commodity_param = request.query_params.get("commodity", "CL").strip().upper()
        commodity = CommodityMaster.objects.filter(code=commodity_param).first()
        if not commodity:
            return Response({"error": f"Commodity '{commodity_param}' not found"}, status=status.HTTP_404_NOT_FOUND)

        latest_date = (
            MarketPriceObservation.objects.filter(
                commodity=commodity,
                delivery_month__startswith="M",
            )
            .order_by("-observation_date")
            .values_list("observation_date", flat=True)
            .first()
        )
        if not latest_date:
            p_last = MarketPriceObservation.objects.filter(commodity=commodity, is_prompt=True).order_by("-observation_date").first()
            latest_date = p_last.observation_date if p_last else date.today()

        def parse_tenor(m_str):
            digits = "".join(ch for ch in m_str if ch.isdigit())
            return int(digits) if digits else 999

        current_obs = list(
            MarketPriceObservation.objects.filter(
                commodity=commodity,
                observation_date=latest_date,
                delivery_month__startswith="M",
            )
        )
        current_obs.sort(key=lambda o: parse_tenor(o.delivery_month))

        prompt_obs = (
            MarketPriceObservation.objects.filter(
                commodity=commodity,
                is_prompt=True,
                observation_date__lte=latest_date,
            )
            .order_by("-observation_date")
            .first()
        )
        spot = float(prompt_obs.close_price or prompt_obs.settlement_price) if prompt_obs and prompt_obs.close_price else (float(current_obs[0].settlement_price) if current_obs else 75.0)

        opt_date = (
            OptionsObservation.objects.filter(
                commodity=commodity,
                observation_date__lte=latest_date,
            )
            .order_by("-observation_date")
            .values_list("observation_date", flat=True)
            .first()
        )
        options_map = {}
        if opt_date:
            options_map = {
                opt.delivery_month: opt
                for opt in OptionsObservation.objects.filter(
                    commodity=commodity,
                    observation_date=opt_date,
                )
            }

        m1_base = float(current_obs[0].settlement_price or current_obs[0].close_price or spot) if current_obs else spot

        contracts = []
        for o in current_obs:
            p_val = float(o.settlement_price or o.close_price or spot)
            tenor_idx = parse_tenor(o.delivery_month)
            if tenor_idx == 1:
                spread = 0.0
                r_yield = 0.0
            else:
                spread = round(p_val - m1_base, 4)
                r_yield = round((m1_base - p_val) / m1_base * (12.0 / tenor_idx) * 100, 2) if tenor_idx > 0 and m1_base > 0 else 0.0
            opt = options_map.get(o.delivery_month)

            contracts.append({
                "tenor": o.delivery_month,
                "month_idx": tenor_idx,
                "settlement_price": p_val,
                "spread_to_prompt": spread,
                "annualized_roll_yield_pct": r_yield,
                "volume": o.volume or 0,
                "atm_iv": float(opt.atm_implied_volatility) if opt and opt.atm_implied_volatility else None,
                "skew_25d": float(opt.skew_25d) if opt and opt.skew_25d else None,
                "put_call_volume_ratio": float(opt.put_call_volume_ratio) if opt and opt.put_call_volume_ratio else None,
                "put_call_oi_ratio": float(opt.put_call_oi_ratio) if opt and opt.put_call_oi_ratio else None,
            })

        def get_curve_at_target_date(target_d):
            best_d = (
                MarketPriceObservation.objects.filter(
                    commodity=commodity,
                    delivery_month__startswith="M",
                    observation_date__lte=target_d,
                )
                .order_by("-observation_date")
                .values_list("observation_date", flat=True)
                .first()
            )
            if not best_d:
                return None, []
            obs = list(
                MarketPriceObservation.objects.filter(
                    commodity=commodity,
                    observation_date=best_d,
                    delivery_month__startswith="M",
                )
            )
            obs.sort(key=lambda o: parse_tenor(o.delivery_month))
            return best_d, [float(o.settlement_price or o.close_price or 0.0) for o in obs]

        d_1w, curve_1w = get_curve_at_target_date(latest_date - timedelta(days=7))
        d_1m, curve_1m = get_curve_at_target_date(latest_date - timedelta(days=30))
        d_1y, curve_1y = get_curve_at_target_date(latest_date - timedelta(days=365))

        m1_price = contracts[0]["settlement_price"] if contracts else spot
        m2_price = contracts[1]["settlement_price"] if len(contracts) > 1 else m1_price
        m12_price = contracts[11]["settlement_price"] if len(contracts) >= 12 else (contracts[-1]["settlement_price"] if contracts else m1_price)

        slope_1m = m1_price - m2_price
        slope_12m = m1_price - m12_price
        if slope_1m > 0.5:
            curve_state = "STRONG_BACKWARDATION"
        elif slope_1m > 0.05:
            curve_state = "MILD_BACKWARDATION"
        elif slope_1m < -0.5:
            curve_state = "SUPER_CONTANGO"
        elif slope_1m < -0.05:
            curve_state = "CONTANGO"
        else:
            curve_state = "FLAT_CURVE"

        return Response({
            "status": "ok",
            "commodity_code": commodity.code,
            "commodity_name": commodity.name,
            "observation_date": latest_date.isoformat(),
            "spot_price": spot,
            "pricing_unit": commodity.pricing_unit.symbol if commodity.pricing_unit else "$",
            "currency_symbol": commodity.pricing_unit.symbol if commodity.pricing_unit else "$",
            "curve_state": curve_state,
            "slope_1m": round(slope_1m, 4),
            "slope_12m": round(slope_12m, 4),
            "contracts": contracts,
            "comparisons": {
                "current": {"date": latest_date.isoformat(), "prices": [c["settlement_price"] for c in contracts]},
                "week_ago": {"date": d_1w.isoformat() if d_1w else None, "prices": curve_1w},
                "month_ago": {"date": d_1m.isoformat() if d_1m else None, "prices": curve_1m},
                "year_ago": {"date": d_1y.isoformat() if d_1y else None, "prices": curve_1y},
            }
        })


class SpreadAnalyticsAPIView(APIView):
    """
    Quantitative Cross-Commodity & Processing Spreads Analytics Engine.
    Supported spreads:
    - `crack_321`: 3:2:1 Refinery Crack Margin (CL, RB, HO)
    - `brent_wti`: Transatlantic Crude Arbitrage (BRENT - CL)
    - `crush`: Soybean Processing Margin (Soymeal + Soyoil - Soybeans)
    - `spark`: Gas-to-Power Thermal Margin (Power - Natural Gas)
    - `calendar`: Prompt Front-Month vs 2nd-Month Roll Spread (M1 - M2)
    """
    def get(self, request, *args, **kwargs):
        spread_type = request.query_params.get("spread_type", "crack_321").strip().lower()
        comm_param = request.query_params.get("commodity", "CL").strip().upper()

        valid_spreads = ["crack_321", "brent_wti", "crush", "spark", "calendar"]
        if spread_type not in valid_spreads:
            return Response(
                {"error": f"Invalid spread_type '{spread_type}'. Supported: {', '.join(valid_spreads)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        time_series = []
        name = ""
        unit = "$/bbl"
        formula = ""

        if spread_type == "crack_321":
            name = "3:2:1 Refinery Crack Margin"
            unit = "$/bbl"
            formula = "(2 × RBOB Gasoline + 1 × Heating Oil - 3 × WTI Crude) / 3"
            cl = CommodityMaster.objects.filter(code="CL").first()
            rb = CommodityMaster.objects.filter(code="RB").first()
            ho = CommodityMaster.objects.filter(code="HO").first()

            if cl and rb and ho:
                cl_map = {o["observation_date"]: float(o["close_price"]) for o in MarketPriceObservation.objects.filter(commodity=cl, is_prompt=True).values("observation_date", "close_price") if o["close_price"]}
                rb_map = {o["observation_date"]: float(o["close_price"]) for o in MarketPriceObservation.objects.filter(commodity=rb, is_prompt=True).values("observation_date", "close_price") if o["close_price"]}
                ho_map = {o["observation_date"]: float(o["close_price"]) for o in MarketPriceObservation.objects.filter(commodity=ho, is_prompt=True).values("observation_date", "close_price") if o["close_price"]}

                common_dates = sorted(set(cl_map.keys()) & set(rb_map.keys()) & set(ho_map.keys()))
                for d in common_dates:
                    c = cl_map[d]
                    r = rb_map[d] / 100.0 if rb_map[d] > 20.0 else rb_map[d]
                    h = ho_map[d] / 100.0 if ho_map[d] > 20.0 else ho_map[d]
                    val = ((2.0 * r * 42.0) + (1.0 * h * 42.0) - (3.0 * c)) / 3.0
                    time_series.append({
                        "date": d.isoformat(),
                        "year": d.year,
                        "week": d.isocalendar()[1],
                        "value": round(val, 2),
                        "legs": {"cl": c, "rb": round(r, 4), "ho": round(h, 4)},
                    })

        elif spread_type == "brent_wti":
            name = "Brent - WTI Quality & Arbitrage Spread"
            unit = "$/bbl"
            formula = "Brent Crude Prompt - WTI Crude Prompt"
            cl = CommodityMaster.objects.filter(code="CL").first()
            brent = CommodityMaster.objects.filter(code="BRENT").first()

            if cl and brent:
                cl_map = {o["observation_date"]: float(o["close_price"]) for o in MarketPriceObservation.objects.filter(commodity=cl, is_prompt=True).values("observation_date", "close_price") if o["close_price"]}
                brent_map = {o["observation_date"]: float(o["close_price"]) for o in MarketPriceObservation.objects.filter(commodity=brent, is_prompt=True).values("observation_date", "close_price") if o["close_price"]}

                common_dates = sorted(set(cl_map.keys()) & set(brent_map.keys()))
                for d in common_dates:
                    val = brent_map[d] - cl_map[d]
                    time_series.append({
                        "date": d.isoformat(),
                        "year": d.year,
                        "week": d.isocalendar()[1],
                        "value": round(val, 2),
                        "legs": {"brent": brent_map[d], "wti": cl_map[d]},
                    })

        elif spread_type == "crush":
            name = "Soybean Processing Crush Margin"
            unit = "$/bu"
            formula = "(0.022 × Meal $/ton + 0.11 × Soyoil ¢/lb) - Soybeans $/bu"
            beans = CommodityMaster.objects.filter(code="SOYBEANS").first()
            oil = CommodityMaster.objects.filter(code="SOYOIL").first()

            if beans and oil:
                b_map = {o["observation_date"]: float(o["close_price"]) for o in MarketPriceObservation.objects.filter(commodity=beans, is_prompt=True).values("observation_date", "close_price") if o["close_price"]}
                o_map = {o["observation_date"]: float(o["close_price"]) for o in MarketPriceObservation.objects.filter(commodity=oil, is_prompt=True).values("observation_date", "close_price") if o["close_price"]}

                common_dates = sorted(set(b_map.keys()) & set(o_map.keys()))
                for d in common_dates:
                    b_bu = b_map[d] / 100.0 if b_map[d] > 100.0 else b_map[d]
                    oil_c = o_map[d]
                    oil_rev = oil_c * 0.11 if oil_c > 1.0 else (oil_c * 100.0) * 0.11
                    meal_rev = 340.0 * 0.022
                    val = (meal_rev + oil_rev) - b_bu
                    time_series.append({
                        "date": d.isoformat(),
                        "year": d.year,
                        "week": d.isocalendar()[1],
                        "value": round(val, 2),
                        "legs": {"beans": round(b_bu, 2), "oil": oil_c, "meal": 340.0},
                    })

        elif spread_type == "spark":
            name = "Gas-to-Power Spark Spread"
            unit = "$/MWh"
            formula = "Power Benchmark ($45/MWh) - (Henry Hub × 7.0 Heat Rate)"
            ng = CommodityMaster.objects.filter(code="NG").first()

            if ng:
                ng_qs = MarketPriceObservation.objects.filter(commodity=ng, is_prompt=True).order_by("observation_date")
                for o in ng_qs:
                    if not o.close_price:
                        continue
                    ng_val = float(o.close_price)
                    ng_mmbtu = ng_val / 100.0 if ng_val > 20.0 else ng_val
                    fuel_cost = ng_mmbtu * 7.0
                    val = 45.0 - fuel_cost
                    d = o.observation_date
                    time_series.append({
                        "date": d.isoformat(),
                        "year": d.year,
                        "week": d.isocalendar()[1],
                        "value": round(val, 2),
                        "legs": {"power": 45.0, "gas": ng_mmbtu},
                    })

        elif spread_type == "calendar":
            name = f"{comm_param} Prompt Calendar Roll Spread (M1 - M2)"
            unit = "$/contract"
            formula = "Contract M1 Settlement - Contract M2 Settlement"
            commodity = CommodityMaster.objects.filter(code=comm_param).first()
            if commodity:
                dates = (
                    MarketPriceObservation.objects.filter(
                        commodity=commodity,
                        delivery_month__in=["M1", "M2"],
                    )
                    .values_list("observation_date", flat=True)
                    .distinct()
                    .order_by("observation_date")
                )
                for d in dates:
                    m1 = MarketPriceObservation.objects.filter(commodity=commodity, delivery_month="M1", observation_date=d).first()
                    m2 = MarketPriceObservation.objects.filter(commodity=commodity, delivery_month="M2", observation_date=d).first()
                    if m1 and m2 and m1.settlement_price and m2.settlement_price:
                        val = float(m1.settlement_price) - float(m2.settlement_price)
                        time_series.append({
                            "date": d.isoformat(),
                            "year": d.year,
                            "week": d.isocalendar()[1],
                            "value": round(val, 4),
                            "legs": {"m1": float(m1.settlement_price), "m2": float(m2.settlement_price)},
                        })

        values = [pt["value"] for pt in time_series]
        latest_val = values[-1] if values else 0.0
        prev_val = values[-2] if len(values) >= 2 else latest_val
        point_change = round(latest_val - prev_val, 4)
        pct_change = round((point_change / abs(prev_val)) * 100.0, 2) if prev_val != 0 else 0.0

        recent_20 = values[-20:] if len(values) >= 20 else values
        ma_20 = round(sum(recent_20) / len(recent_20), 4) if recent_20 else latest_val

        recent_252 = values[-252:] if len(values) >= 252 else values
        high_52w = max(recent_252) if recent_252 else latest_val
        low_52w = min(recent_252) if recent_252 else latest_val

        std_1y = float(np.std(recent_252)) if len(recent_252) > 1 else 1.0
        mean_1y = float(np.mean(recent_252)) if recent_252 else latest_val
        zscore_1y = round(float((latest_val - mean_1y) / (std_1y or 1e-6)), 2)

        regime = "NORMAL_RANGE"
        if zscore_1y >= 1.5:
            regime = "MARGIN_EXPANSION_HIGH"
        elif zscore_1y >= 0.5:
            regime = "ELEVATED_MARGIN"
        elif zscore_1y <= -1.5:
            regime = "MARGIN_COMPRESSION_LOW"
        elif zscore_1y <= -0.5:
            regime = "DEPRESSED_MARGIN"

        wk_acc = {}
        for pt in time_series:
            wk_acc.setdefault(pt["week"], []).append(pt["value"])
        seasonality_weekly = {
            str(w): round(sum(vals) / len(vals), 2)
            for w, vals in sorted(wk_acc.items())
        }

        return Response({
            "status": "ok",
            "spread_type": spread_type,
            "name": name,
            "unit": unit,
            "formula": formula,
            "total_observations": len(time_series),
            "latest": {
                "date": time_series[-1]["date"] if time_series else None,
                "value": latest_val,
                "point_change": point_change,
                "pct_change": pct_change,
                "ma_20": ma_20,
                "high_52w": high_52w,
                "low_52w": low_52w,
                "zscore_1y": zscore_1y,
                "regime": regime,
                "legs": time_series[-1]["legs"] if time_series else {},
            },
            "time_series": time_series,
            "seasonality_weekly": seasonality_weekly,
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
