"""
Feature Pipeline & Extraction Orchestrator.

Queries minimum necessary point-in-time observations from the database,
executes vectorized feature modules, and returns a fully validated
LiveQuantFeaturePackage.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
import numpy as np

from apps.commodities.models import CommodityMaster
from apps.market_data.models import (
    MarketPriceObservation,
    FundamentalObservation,
    CommitmentOfTradersObservation,
)
from apps.news_intel.models import MarketCatalystEvent

from .config import DEFAULT_FEATURE_CONFIG, FeatureConfig
from .data_quality import QualityStatus, safe_float
from .schemas import (
    LiveQuantFeaturePackage,
    PriceFeatures,
    TrendFeatures,
    MomentumFeatures,
    VolatilityFeatures,
    VolumeFeatures,
    StructureFeatures,
    VwapFeatures,
    CurveFeatures,
    RelativeValueFeatures,
    OrderFlowFeatures,
    LiquidityFeatures,
    FundamentalsFeatures,
    EventsFeatures,
    RegimeFeatures,
    DivergenceFeatures,
    QuantitativeScores,
)
from .price import calculate_price_features
from .trend import calculate_trend_features
from .momentum import calculate_momentum_features, compute_rsi
from .volatility import calculate_volatility_features
from .location import calculate_location_features
from .volume import calculate_volume_features
from .vwap import calculate_vwap_features
from .market_structure import calculate_market_structure_features
from .support_resistance import calculate_sr_features
from .futures_curve import calculate_curve_features
from .relative_value import calculate_relative_value_features
from .order_flow import calculate_order_flow_features
from .liquidity import calculate_liquidity_features
from .fundamentals import calculate_fundamental_features
from .events import calculate_event_features
from .regime import determine_market_regime
from .divergence import calculate_divergence_features
from .scoring import compute_quantitative_scores


class FeaturePipeline:
    """End-to-end pipeline extracting live quantitative features for a given commodity."""

    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or DEFAULT_FEATURE_CONFIG

    def extract_features(
        self,
        commodity_code: str,
        timeframe: str = "1D",
        intraday_data: Optional[Dict] = None,
    ) -> LiveQuantFeaturePackage:
        """
        Extracts features for a given commodity code.
        """
        code = commodity_code.upper()
        commodity = CommodityMaster.objects.filter(code__iexact=code).first()
        if not commodity:
            raise ValueError(f"Commodity with code '{code}' does not exist.")

        # 1. Fetch minimum required price observations (e.g. 250 bars for 200 EMA & 1Y Vol)
        price_obs = list(
            MarketPriceObservation.objects.filter(commodity=commodity, is_prompt=True)
            .order_by("observation_date")
            .values_list("settlement_price", "close_price", "open_price", "high_price", "low_price", "volume", "open_interest")
        )[-252:]

        if not price_obs:
            # Synthetic fallback when brand new or empty database
            prices = np.array([75.0, 75.5, 76.0])
            highs = prices * 1.01
            lows = prices * 0.99
            volumes = np.array([100000, 120000, 110000])
            oi_series = np.array([1500000, 1510000, 1505000])
            quality_status = QualityStatus.INSUFFICIENT_HISTORY.value
        else:
            prices_raw = [float(p[0] or p[1] or 0.0) for p in price_obs]
            highs_raw = [float(p[3] or p[0] or 0.0) for p in price_obs]
            lows_raw = [float(p[4] or p[0] or 0.0) for p in price_obs]
            volumes_raw = [int(p[5] or 0) for p in price_obs]
            oi_raw = [int(p[6] or 0) for p in price_obs]

            prices = np.array(prices_raw)
            highs = np.array(highs_raw)
            lows = np.array(lows_raw)
            volumes = np.array(volumes_raw)
            oi_series = np.array(oi_raw)
            quality_status = QualityStatus.VALID.value if len(prices) >= 20 else QualityStatus.INSUFFICIENT_HISTORY.value

        # 2. Extract Price Features
        intraday_rets = (intraday_data or {}).get("returns")
        price_dict = calculate_price_features(prices, intraday_returns=intraday_rets, lookback_window=self.config.lookback_short)

        # 3. Extract Trend Features
        trend_dict = calculate_trend_features(
            prices, highs=highs, lows=lows,
            period_fast=self.config.ema_fast,
            period_medium=self.config.ema_medium,
            period_slow=self.config.ema_slow,
            adx_period=self.config.adx_period,
        )

        # 4. Extract Momentum Features
        momentum_dict = calculate_momentum_features(
            prices,
            rsi_period=self.config.rsi_period,
            macd_fast=self.config.macd_fast,
            macd_slow=self.config.macd_slow,
            macd_signal=self.config.macd_signal,
        )

        # 5. Extract Volatility Features
        volatility_dict = calculate_volatility_features(
            prices, highs=highs, lows=lows,
            atr_period=self.config.atr_period,
            realized_vol_window=self.config.realized_vol_period,
        )

        # 6. Extract Volume Features
        volume_dict = calculate_volume_features(volumes, rvol_window=self.config.rvol_window)

        # 7. Extract VWAP Features
        vwap_dict = calculate_vwap_features(prices, volumes, highs=highs, lows=lows)

        # 8. Extract Market Structure & Range Location
        structure_base = calculate_market_structure_features(prices, highs=highs, lows=lows, atr=volatility_dict["atr"])
        location_dict = calculate_location_features(prices, highs=highs, lows=lows, vwap=vwap_dict["vwap"])
        sr_dict = calculate_sr_features(prices, highs=highs, lows=lows, atr=volatility_dict["atr"])

        # Combined Structure Features
        structure_payload = {
            "state": structure_base["state"],
            "range_position_20d": location_dict["range_position_20d"],
            "range_position_60d": location_dict["range_position_60d"],
            "nearest_resistance_distance_pct": sr_dict["nearest_resistance_distance_pct"],
            "nearest_support_distance_pct": sr_dict["nearest_support_distance_pct"],
            "nearest_resistance": sr_dict["nearest_resistance"],
            "nearest_support": sr_dict["nearest_support"],
            "swing_structure": structure_base["swing_structure"],
            "breakout_confirmed": structure_base["breakout_confirmed"],
        }

        # 9. Extract Futures Curve Features
        # Query active curve contract settlements
        latest_date = MarketPriceObservation.objects.filter(commodity=commodity).order_by("-observation_date").values_list("observation_date", flat=True).first()
        if latest_date:
            curve_obs = list(
                MarketPriceObservation.objects.filter(commodity=commodity, observation_date=latest_date)
                .exclude(delivery_month="PROMPT")
                .order_by("delivery_month")
                .values_list("settlement_price", flat=True)[:12]
            )
            curve_prices = [float(p or price_dict["last"]) for p in curve_obs]
        else:
            curve_prices = [price_dict["last"], price_dict["last"] * 0.995, price_dict["last"] * 0.99]

        if not curve_prices or len(curve_prices) < 2:
            curve_prices = [price_dict["last"], price_dict["last"] * 0.995, price_dict["last"] * 0.99]

        curve_dict = calculate_curve_features(curve_prices)

        # 10. Extract Relative Value Features
        peer_code = self.config.relative_value_pairs.get(code)
        if peer_code:
            peer_commodity = CommodityMaster.objects.filter(code__iexact=peer_code).first()
            if peer_commodity:
                peer_raw = list(
                    MarketPriceObservation.objects.filter(commodity=peer_commodity, is_prompt=True)
                    .order_by("observation_date")
                    .values_list("settlement_price", "close_price")
                )[-min(len(prices), 60):]
                peer_prices = np.array([float(p[0] or p[1] or 0.0) for p in peer_raw]) if peer_raw else None
            else:
                peer_prices = None
            rv_dict = calculate_relative_value_features(prices, peer_prices, pair_name=f"{code}-{peer_code}")
        else:
            rv_dict = calculate_relative_value_features(prices, None, pair_name="NONE")

        # 11. Extract Order Flow & Liquidity Features
        of_data = (intraday_data or {}).get("order_flow", {})
        order_flow_dict = calculate_order_flow_features(
            buy_volume=of_data.get("buy_volume"),
            sell_volume=of_data.get("sell_volume"),
            cumulative_delta=of_data.get("cumulative_delta"),
        )

        lq_data = (intraday_data or {}).get("liquidity", {})
        liquidity_dict = calculate_liquidity_features(
            bid=lq_data.get("bid"),
            ask=lq_data.get("ask"),
            bid_depth=lq_data.get("bid_depth"),
            ask_depth=lq_data.get("ask_depth"),
        )

        # 12. Extract Fundamental Features
        latest_fund = (
            FundamentalObservation.objects.filter(variable__commodity=commodity)
            .select_related("variable")
            .order_by("-observation_date")
            .first()
        )
        if latest_fund and latest_fund.value:
            f_val = float(latest_fund.value)
            f_ref = f_val * 1.05  # Standard seasonal baseline estimate
            fund_dict = calculate_fundamental_features(
                variable_name=latest_fund.variable.code,
                current_value=f_val,
                reference_normal=f_ref,
            )
        else:
            fund_dict = calculate_fundamental_features(None, None, None)

        # 13. Extract Event Features
        latest_event = (
            MarketCatalystEvent.objects.filter(primary_commodity=commodity)
            .order_by("-scheduled_datetime_utc")
            .first()
        )
        if latest_event and latest_event.actual_value is not None and latest_event.consensus_expectation is not None:
            ev_dict = calculate_event_features(
                event_name=latest_event.name,
                actual=float(latest_event.actual_value),
                forecast=float(latest_event.consensus_expectation),
            )
        else:
            ev_dict = calculate_event_features(None, None, None)

        # 14. Determine Market Regime
        regime_dict = determine_market_regime(
            trend_state=trend_dict["trend_state"],
            volatility_regime=volatility_dict["regime"],
            momentum_state=momentum_dict["momentum_state"],
        )

        # 15. Detect Divergences
        rsi_series = compute_rsi(prices, period=self.config.rsi_period)
        divergence_dict = calculate_divergence_features(
            prices=prices,
            rsi_series=rsi_series,
            volumes=volumes,
            open_interest=oi_series if len(oi_series) == len(prices) else None,
            timeframe=timeframe,
        )

        # 16. Compute Quantitative Scores
        scores_dict = compute_quantitative_scores(
            trend_dict=trend_dict,
            momentum_dict=momentum_dict,
            volatility_dict=volatility_dict,
            volume_dict=volume_dict,
            structure_dict=structure_payload,
            curve_dict=curve_dict,
            relative_value_dict=rv_dict,
            fundamentals_dict=fund_dict,
            events_dict=ev_dict,
        )

        # 17. Assemble and Validate Pydantic Schema
        return LiveQuantFeaturePackage(
            instrument=commodity.code,
            name=commodity.name,
            sector=commodity.sector,
            timestamp=datetime.now(timezone.utc).isoformat(),
            timeframe=timeframe,
            data_quality=quality_status,
            price=PriceFeatures(**price_dict),
            trend=TrendFeatures(**trend_dict),
            momentum=MomentumFeatures(**momentum_dict),
            volatility=VolatilityFeatures(**volatility_dict),
            volume=VolumeFeatures(**volume_dict),
            structure=StructureFeatures(**structure_payload),
            vwap=VwapFeatures(**vwap_dict),
            curve=CurveFeatures(**curve_dict),
            relative_value=RelativeValueFeatures(**rv_dict),
            order_flow=OrderFlowFeatures(**order_flow_dict),
            liquidity=LiquidityFeatures(**liquidity_dict),
            fundamentals=FundamentalsFeatures(**fund_dict),
            events=EventsFeatures(**ev_dict),
            regime=RegimeFeatures(**regime_dict),
            divergence=DivergenceFeatures(**divergence_dict),
            scores=QuantitativeScores(**scores_dict),
        )
