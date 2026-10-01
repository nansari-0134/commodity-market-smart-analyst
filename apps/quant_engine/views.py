"""
REST API Views for Quantitative Research & Forward Curves Engine.
"""
import numpy as np
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.commodities.models import CommodityMaster
from apps.market_data.models import MarketPriceObservation, OptionsObservation
from apps.quant_engine.core import compute_comprehensive_seasonality_profile
from apps.quant_engine.core.seasonality_methods import evaluate_40_seasonality_methods
from apps.quant_engine.models import DiscoveryRegistry, EvidencePackageSnapshot
from apps.quant_engine.serializers import DiscoveryRegistrySerializer, EvidencePackageSnapshotSerializer
from apps.quant_engine.services.evidence_builder import EvidencePackageBuilder


class QuantitativeEvidencePackageView(APIView):
    """
    Generate or retrieve the complete Quantitative Evidence Package (Section 5.12).
    
    Query Parameters:
        - `commodity`: Canonical commodity code (e.g. 'CL', 'BRENT', 'NG', 'ZC') [default: CL]
        - `persist`: Set to 'true' to store snapshot in EvidencePackageSnapshot and DiscoveryRegistry
    """
    def get(self, request):
        commodity_code = request.query_params.get("commodity", "CL").upper()
        persist = request.query_params.get("persist", "false").lower() == "true"
        
        try:
            builder = EvidencePackageBuilder(commodity_code)
            package = builder.build(persist_snapshot=persist)
            return Response(package.model_dump(mode="json"))
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to calculate evidence package: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketStateView(APIView):
    """
    Retrieve market price structure, multi-horizon returns, volatility, and volume metrics.
    """
    def get(self, request):
        commodity_code = request.query_params.get("commodity", "CL").upper()
        try:
            builder = EvidencePackageBuilder(commodity_code)
            package = builder.build(persist_snapshot=False)
            return Response({
                "commodity": commodity_code,
                "as_of": package.as_of,
                "market_state": package.market_state.model_dump(),
                "positioning": package.positioning_state.model_dump(),
                "divergences": [d.model_dump() for d in package.divergences],
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class ForwardCurveView(APIView):
    """
    Retrieve forward curve continuous spline interpolation, slope analytics,
    and individual contract delivery months (M1 through M24) with options surfaces.
    """
    def get(self, request):
        commodity_code = request.query_params.get("commodity", "CL").upper()
        try:
            builder = EvidencePackageBuilder(commodity_code)
            package = builder.build(persist_snapshot=False)
            
            commodity = CommodityMaster.objects.filter(code=commodity_code).first()
            contracts_data = []
            if commodity:
                from apps.market_data.models import MarketPriceObservation, OptionsObservation
                latest_date = package.as_of
                curve_obs = list(
                    MarketPriceObservation.objects.filter(
                        commodity=commodity,
                        observation_date=latest_date,
                        delivery_month__startswith="M",
                    )
                )
                def parse_tenor(m_str):
                    digits = "".join(c for c in m_str if c.isdigit())
                    return int(digits) if digits else 999

                curve_obs.sort(key=lambda o: parse_tenor(o.delivery_month))

                options_map = {
                    opt.delivery_month: opt
                    for opt in OptionsObservation.objects.filter(
                        commodity=commodity,
                        observation_date=latest_date,
                    )
                }

                spot = package.market_state.spot_price
                for obs in curve_obs:
                    price = float(obs.settlement_price or obs.close_price or spot)
                    spread = round(price - spot, 4)
                    tenor_idx = parse_tenor(obs.delivery_month)
                    roll_yield = round((spot - price) / spot * (12.0 / tenor_idx) * 100, 2) if tenor_idx > 0 and spot > 0 else 0.0

                    opt = options_map.get(obs.delivery_month)
                    options_dict = {
                        "atm_implied_volatility": float(opt.atm_implied_volatility) if opt and opt.atm_implied_volatility else None,
                        "skew_25d": float(opt.skew_25d) if opt and opt.skew_25d else None,
                        "put_call_volume_ratio": float(opt.put_call_volume_ratio) if opt and opt.put_call_volume_ratio else None,
                        "put_call_oi_ratio": float(opt.put_call_oi_ratio) if opt and opt.put_call_oi_ratio else None,
                    } if opt else None

                    contracts_data.append({
                        "tenor": obs.delivery_month,
                        "settlement_price": price,
                        "spread_to_prompt": spread,
                        "annualized_roll_yield_pct": roll_yield,
                        "volume": obs.volume,
                        "is_preliminary": obs.is_preliminary,
                        "options": options_dict,
                    })

            return Response({
                "commodity": commodity_code,
                "as_of": package.as_of,
                "spot_price": package.market_state.spot_price,
                "curve_state": package.market_state.curve_state,
                "prompt_spread": package.market_state.prompt_spread_1m_2m,
                "roll_yield_1y": package.market_state.roll_yield_1y,
                "butterfly": package.market_state.butterfly_curvature,
                "contract_count": len(contracts_data),
                "contracts": contracts_data,
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class SpreadsView(APIView):
    """
    Retrieve transformation spreads (3:2:1 Crack, Soybean Crush, Spark Spread).
    """
    def get(self, request):
        commodity_code = request.query_params.get("commodity", "CL").upper()
        try:
            builder = EvidencePackageBuilder(commodity_code)
            package = builder.build(persist_snapshot=False)
            return Response({
                "commodity": commodity_code,
                "as_of": package.as_of,
                "spreads": package.spreads.model_dump(),
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class CrossCommodityView(APIView):
    """
    Retrieve logical commodity complex information, cointegration tests, and macro factors.
    """
    def get(self, request):
        commodity_code = request.query_params.get("commodity", "CL").upper()
        try:
            builder = EvidencePackageBuilder(commodity_code)
            package = builder.build(persist_snapshot=False)
            return Response({
                "commodity": commodity_code,
                "as_of": package.as_of,
                "cross_commodity": package.cross_commodity.model_dump(),
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class SeasonalityView(APIView):
    """
    Retrieve historical seasonality envelopes, directional tenure patterns, and forward 1M volatility peak forecast,
    plus full 20-year Day-of-Year normalized trajectory and 2005-2026 monthly returns matrix.
    """
    def get(self, request):
        commodity_code = request.query_params.get("commodity", "CL").upper()
        try:
            builder = EvidencePackageBuilder(commodity_code)
            package = builder.build(persist_snapshot=False)

            from apps.market_data.models import MarketPriceObservation
            from apps.quant_engine.core import compute_comprehensive_seasonality_profile
            import numpy as np

            commodity = CommodityMaster.objects.filter(code=commodity_code).first()
            profile_20y = {}
            if commodity:
                obs = list(
                    MarketPriceObservation.objects.filter(
                        commodity=commodity,
                        is_prompt=True,
                        observation_date__lte=package.as_of.date(),
                    )
                    .order_by("observation_date")
                    .values_list("observation_date", "close_price")
                )
                dates = [r[0] for r in obs]
                prices = np.array([float(r[1]) for r in obs])
                profile_20y = compute_comprehensive_seasonality_profile(
                    dates=dates,
                    prices=prices,
                    current_date=package.as_of.date(),
                    commodity_code=commodity_code,
                )

            return Response({
                "commodity": commodity_code,
                "as_of": package.as_of,
                "seasonality": package.seasonality.model_dump(),
                "profile_20y": profile_20y,
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class DiscoveryRegistryListView(generics.ListAPIView):
    """
    List validated quantitative discoveries and regime changes.
    """
    serializer_class = DiscoveryRegistrySerializer

    def get_queryset(self):
        qs = DiscoveryRegistry.objects.select_related("commodity", "related_commodity").all()
        commodity_code = self.request.query_params.get("commodity")
        if commodity_code:
            qs = qs.filter(commodity__code=commodity_code.upper())
            
        discovery_type = self.request.query_params.get("type")
        if discovery_type:
            qs = qs.filter(discovery_type=discovery_type.upper())
            
        active_only = self.request.query_params.get("active")
        if active_only and active_only.lower() == "true":
            qs = qs.filter(is_active=True)
            
        return qs


class SeasonalityMethodsCatalogView(APIView):
    """
    Evaluates and returns the complete 40-Method Seasonality Matrix for a commodity.
    Includes calendar, volatility, curve, fundamental, statistical, and regime methods.
    """

    def get(self, request):
        from apps.quant_engine.core.seasonality_methods import evaluate_40_seasonality_methods
        commodity_code = request.query_params.get("commodity", "CL").upper()
        try:
            builder = EvidencePackageBuilder(commodity_code=commodity_code)
            package = builder.build(persist_snapshot=False)

            obs = list(
                MarketPriceObservation.objects.filter(
                    commodity=builder.commodity,
                    is_prompt=True,
                    observation_date__lte=package.as_of.date(),
                )
                .order_by("observation_date")
                .values_list("observation_date", "close_price")
            )
            dates = [r[0] for r in obs]
            prices = np.array([float(r[1]) for r in obs])

            profile_20y = compute_comprehensive_seasonality_profile(
                dates=dates,
                prices=prices,
                current_date=package.as_of.date(),
                commodity_code=commodity_code,
            )

            evaluated = evaluate_40_seasonality_methods(
                dates=dates,
                prices=prices,
                current_date=package.as_of.date(),
                commodity_code=commodity_code,
                base_seasonality_profile=profile_20y,
            )

            return Response({
                "commodity": commodity_code,
                "as_of": package.as_of,
                "total_methods": len(evaluated["methods"]),
                "sections": evaluated["sections"],
                "methods": evaluated["methods"],
                "analytical_payloads": evaluated["analytical_payloads"],
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

