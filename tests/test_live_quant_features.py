"""
Comprehensive Unit & Integration Test Suite for the Live Quantitative Feature Engine.

Validates:
1. Mathematical correctness of all 20 vectorized feature modules
2. Data quality guards, NaN/inf protections, and unavailable handling
3. Pydantic v2 schema compliance with Section 21 specification
4. Incremental LiveFeatureProcessor rolling buffer updates
5. End-to-end FeaturePipeline database extraction
6. REST API endpoint GET /api/quant/live-features/
"""
import pytest
import numpy as np
from rest_framework.test import APIClient
from rest_framework import status

from apps.commodities.models import CommodityMaster
from apps.market_data.models import MarketPriceObservation
from apps.quant_engine.features.config import FeatureConfig, DEFAULT_FEATURE_CONFIG
from apps.quant_engine.features.data_quality import safe_float, safe_div, validate_series, QualityStatus
from apps.quant_engine.features.price import calculate_price_features
from apps.quant_engine.features.statistics import rolling_zscore, rolling_percentile, robust_mad_zscore
from apps.quant_engine.features.trend import compute_ema, compute_adx, calculate_trend_features
from apps.quant_engine.features.momentum import compute_rsi, compute_macd, calculate_momentum_features
from apps.quant_engine.features.volatility import compute_atr, calculate_volatility_features
from apps.quant_engine.features.location import calculate_range_position, calculate_location_features
from apps.quant_engine.features.volume import calculate_volume_features
from apps.quant_engine.features.vwap import compute_vwap, calculate_vwap_features
from apps.quant_engine.features.market_structure import calculate_market_structure_features, classify_swing_structure
from apps.quant_engine.features.support_resistance import calculate_sr_features, evaluate_level_strength
from apps.quant_engine.features.futures_curve import calculate_curve_features, classify_curve_state
from apps.quant_engine.features.relative_value import calculate_relative_value_features
from apps.quant_engine.features.order_flow import calculate_order_flow_features
from apps.quant_engine.features.liquidity import calculate_liquidity_features
from apps.quant_engine.features.fundamentals import calculate_fundamental_features
from apps.quant_engine.features.events import calculate_event_features
from apps.quant_engine.features.regime import determine_market_regime
from apps.quant_engine.features.divergence import calculate_divergence_features, detect_indicator_divergence
from apps.quant_engine.features.scoring import compute_quantitative_scores
from apps.quant_engine.features.llm_formatter import format_llm_json, format_llm_prompt_context
from apps.quant_engine.features.live_processor import LiveFeatureProcessor
from apps.quant_engine.features.pipeline import FeaturePipeline


@pytest.mark.django_db
class TestLiveQuantFeatureEngine:
    """Complete test suite for live quantitative features."""

    def test_data_quality_and_guards(self):
        """Tests NaN, inf, and zero division guards."""
        assert safe_float(None) == 0.0
        assert safe_float(float("nan"), default=5.0) == 5.0
        assert safe_float(float("inf"), default=-1.0) == -1.0
        assert safe_float(12.34567, round_digits=2) == 12.35

        assert safe_div(10.0, 0.0) == 0.0
        assert safe_div(10.0, float("nan")) == 0.0
        assert safe_div(10.0, 2.0) == 5.0

        is_valid, qual = validate_series(np.array([1.0]), min_length=2)
        assert not is_valid
        assert qual == QualityStatus.INSUFFICIENT_HISTORY

        is_valid, qual = validate_series(np.array([10.0, 11.0, 12.0]), min_length=2)
        assert is_valid
        assert qual == QualityStatus.VALID

    def test_price_returns_and_percentiles(self):
        """Tests price returns, acceleration, and rolling percentile."""
        prices = np.linspace(70.0, 80.0, 25)
        res = calculate_price_features(prices, intraday_returns={"5m": 0.002, "1h": 0.01})

        assert res["last"] == 80.0
        assert res["return_1d"] > 0
        assert res["log_return_1d"] > 0
        assert res["return_5m"] == 0.002
        assert res["return_1h"] == 0.01
        assert res["percentile_20d"] == 100.0  # Highest price
        assert res["zscore_20d"] > 1.5

    def test_statistical_normalization(self):
        """Tests rolling Z-scores, percentiles, and robust MAD."""
        data = np.array([10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 20.0])
        z = rolling_zscore(data, window=7)
        pct = rolling_percentile(data, window=7)
        mad_z = robust_mad_zscore(data, window=7)

        assert z > 1.5
        assert pct == 100.0
        assert mad_z > 1.5

    def test_trend_ema_and_adx(self):
        """Tests EMA trend structure, distance %, and ADX calculation."""
        # Strongly trending upward series
        prices = np.linspace(50.0, 100.0, 60)
        highs = prices * 1.01
        lows = prices * 0.99

        res = calculate_trend_features(prices, highs=highs, lows=lows, period_fast=10, period_medium=20, period_slow=30)
        assert res["ema_structure"] == "bullish"
        assert res["ema_slope"] == "positive"
        assert res["trend_state"] in ["strong_bullish", "weak_bullish"]
        assert res["dist_ema20_pct"] > 0
        assert res["adx"] >= 15.0

    def test_momentum_rsi_and_macd(self):
        """Tests RSI calculations, percentiles, and MACD crossovers."""
        # Upward price drift
        prices = np.array([50.0 + (i * 0.5) + (np.sin(i) * 0.2) for i in range(50)])
        res = calculate_momentum_features(prices)

        assert res["rsi"] > 50.0
        assert res["rsi_percentile"] > 50.0
        assert res["momentum_state"] in ["strengthening", "overbought", "neutral"]
        assert "macd" in res
        assert "macd_histogram" in res

    def test_volatility_atr_and_realized_vol(self):
        """Tests ATR in price units, % of price, and annualized realized volatility."""
        prices = np.array([75.0 + (np.sin(i * 0.5) * 3.0) for i in range(40)])
        highs = prices + 1.5
        lows = prices - 1.5

        res = calculate_volatility_features(prices, highs=highs, lows=lows)
        assert res["atr"] > 1.0
        assert res["atr_pct"] > 0
        assert res["realized_volatility"] > 0
        assert res["regime"] in ["low", "normal", "high", "extreme"]

    def test_location_and_support_resistance(self):
        """Tests high-low range position and nearest structural levels."""
        prices = np.array([70.0, 72.0, 75.0, 78.0, 80.0])
        res_loc = calculate_location_features(prices)
        assert res_loc["range_position_20d"] == 100.0
        assert res_loc["nearest_resistance"] == 80.0
        assert res_loc["nearest_support"] == 70.0

        res_sr = calculate_sr_features(prices, atr=1.5)
        assert res_sr["nearest_resistance"] >= 80.0
        assert res_sr["nearest_support"] <= 80.0

    def test_volume_and_vwap(self):
        """Tests RVOL and VWAP deviation."""
        prices = np.array([70.0, 71.0, 72.0, 75.0])
        volumes = np.array([100000, 100000, 100000, 250000])

        res_vol = calculate_volume_features(volumes, rvol_window=4)
        assert res_vol["relative_volume"] >= 2.0
        assert res_vol["state"] == "unusually_high"

        res_vwap = calculate_vwap_features(prices, volumes)
        assert res_vwap["vwap"] > 70.0
        assert res_vwap["vwap_deviation_pct"] > 0.0

    def test_market_structure_and_breakouts(self):
        """Tests Higher Highs / Higher Lows structure and breakout confirmation."""
        # Upward zig-zag forming higher highs and higher lows
        prices = np.array([70.0, 72.0, 74.0, 73.0, 75.0, 77.0, 76.0, 79.0, 81.0])
        highs = prices + 0.5
        lows = prices - 0.5

        res = calculate_market_structure_features(prices, highs=highs, lows=lows, atr=1.0, pivot_window=1)
        assert res["swing_structure"] in ["higher_highs_higher_lows", "range", "transition"]
        assert "breakout_confirmed" in res

    def test_futures_curve_and_slopes(self):
        """Tests calendar spreads (F1-F2, F2-F3, F1-F3) and contango/backwardation states."""
        # Backwardation: F1 > F2 > F3
        prices_back = [78.0, 76.5, 75.0, 73.0]
        res_back = calculate_curve_features(prices_back)
        assert res_back["spread_f1_f2"] == 1.5
        assert res_back["spread_f2_f3"] == 1.5
        assert res_back["spread_f1_f3"] == 3.0
        assert res_back["curve_state"] in ["backwardation", "strong_backwardation"]
        assert res_back["curve_slope_annualized"] < 0

        # Contango: F1 < F2 < F3
        prices_cont = [70.0, 71.5, 73.0, 76.0]
        res_cont = calculate_curve_features(prices_cont)
        assert res_cont["spread_f1_f2"] == -1.5
        assert res_cont["curve_state"] in ["contango", "strong_contango"]
        assert res_cont["curve_slope_annualized"] > 0

    def test_relative_value_correlations(self):
        """Tests rolling correlation and spread Z-score against a peer."""
        p1 = np.linspace(70.0, 80.0, 20)
        p2 = np.linspace(75.0, 85.0, 20)

        res = calculate_relative_value_features(p1, p2, pair_name="CL-BRENT")
        assert res["benchmark_pair"] == "CL-BRENT"
        assert res["rolling_correlation"] >= 0.90

    def test_order_flow_and_liquidity(self):
        """Tests aggressive delta and top-of-book liquidity metrics."""
        # Available
        res_of = calculate_order_flow_features(buy_volume=60000, sell_volume=40000, cumulative_delta=20000)
        assert res_of["is_available"] is True
        assert res_of["imbalance"] == 0.2
        assert res_of["delta_direction"] == "neutral"

        # Unavailable
        res_of_na = calculate_order_flow_features(None, None)
        assert res_of_na["is_available"] is False
        assert res_of_na["imbalance"] is None

        # Liquidity
        res_lq = calculate_liquidity_features(bid=75.10, ask=75.12, tick_size=0.01)
        assert res_lq["is_available"] is True
        assert res_lq["bid_ask_spread"] == 0.02
        assert res_lq["bid_ask_spread_ticks"] == 2.0

    def test_fundamentals_and_events(self):
        """Tests inventory deviations from normal, momentum, and catalyst surprises."""
        res_fund = calculate_fundamental_features(
            variable_name="CRUDE_CUSHING_STOCKS",
            current_value=25.0,
            reference_normal=32.0,
            prior_value=26.0,
        )
        assert res_fund["deviation_abs"] == -7.0
        assert res_fund["deviation_pct"] < 0
        assert res_fund["inventory_zscore"] < 0
        assert res_fund["fundamental_momentum"] in ["drawing", "tightening"]

        res_ev = calculate_event_features(
            event_name="EIA Weekly Petroleum",
            actual=-2.5,
            forecast=1.0,
            historical_std=2.0,
            price_before=75.0,
            price_after_1h=76.2,
        )
        assert res_ev["surprise"] == -3.5
        assert res_ev["standardized_surprise"] < 0
        assert res_ev["immediate_reaction_1h_pct"] > 1.0

    def test_regime_and_divergence(self):
        """Tests combined market regime and multi-factor divergence detection."""
        reg = determine_market_regime("strong_bullish", "high")
        assert reg["overall"] == "bullish_high_volatility"

        # Bearish divergence: Price higher high, but RSI lower high
        prices = np.array([70.0, 72.0, 71.0, 75.0, 73.0, 77.0, 78.0])
        rsi_series = np.array([60.0, 68.0, 62.0, 75.0, 70.0, 66.0, 64.0])
        div_res = detect_indicator_divergence(prices, rsi_series, "price_vs_rsi", window=6)
        assert div_res is not None
        assert div_res["direction"] == "bearish"

    def test_quantitative_scores(self):
        """Tests transparent composite multi-factor quantitative scores."""
        scores = compute_quantitative_scores(
            trend_dict={"ema_structure": "bullish", "adx": 35.0, "dist_ema20_pct": 2.0},
            momentum_dict={"rsi": 65.0, "histogram_direction": "increasing"},
            volatility_dict={"vol_percentile": 60.0},
            volume_dict={"relative_volume": 1.4},
            structure_dict={"swing_structure": "higher_highs_higher_lows", "range_position_20d": 80.0, "state": "normal"},
            curve_dict={"curve_state": "backwardation", "spread_zscore": 1.2},
            relative_value_dict={"spread_zscore": 0.5},
            fundamentals_dict={"inventory_zscore": -1.5},
            events_dict={"standardized_surprise": 0.8},
        )
        assert -1.0 <= scores["trend_score"] <= 1.0
        assert -1.0 <= scores["momentum_score"] <= 1.0
        assert 0.0 <= scores["volatility_score"] <= 1.0
        assert 0.0 <= scores["volume_score"] <= 1.0
        assert -1.0 <= scores["overall_composite_score"] <= 1.0
        assert scores["overall_composite_score"] > 0.3  # Net bullish setup

    def test_live_feature_processor_incremental(self):
        """Tests LiveFeatureProcessor in-memory buffer and tick updates."""
        proc = LiveFeatureProcessor()
        prices = np.linspace(70.0, 75.0, 30)
        highs = prices + 0.5
        lows = prices - 0.5
        volumes = np.full(30, 100000)

        proc.warm_up("CL", prices, highs, lows, volumes)
        package = proc.process_tick("CL", "WTI Crude", "ENERGY", price=75.80, volume=150000)

        assert package.instrument == "CL"
        assert package.price.last == 75.80
        assert package.volume.volume == 150000
        assert package.data_quality == "VALID"

    def _setup_test_commodity(self, code="CL"):
        from apps.metadata.models import UnitMaster, UnitType
        from apps.exchanges.models import ExchangeMaster
        from apps.commodities.models import CommoditySector
        from datetime import date, timedelta

        pricing_unit, _ = UnitMaster.objects.get_or_create(
            code="USD_BBL",
            defaults={"name": "US Dollar per Barrel", "symbol": "USD_BBL", "unit_type": UnitType.PRICE_PER_UNIT},
        )
        lot_unit, _ = UnitMaster.objects.get_or_create(
            code="BBL",
            defaults={"name": "Barrels", "symbol": "BBL", "unit_type": UnitType.VOLUME},
        )
        exchange, _ = ExchangeMaster.objects.get_or_create(
            code="NYMEX_TEST",
            defaults={
                "mic": "XTST",
                "name": "New York Mercantile Exchange Test",
                "country": "USA",
                "city": "New York",
                "timezone": "America/New_York",
            },
        )
        commodity, _ = CommodityMaster.objects.get_or_create(
            code=code,
            defaults={
                "name": "Light Sweet Crude Oil",
                "sector": CommoditySector.ENERGY,
                "group": "CRUDE_OIL",
                "primary_exchange": exchange,
                "base_unit": lot_unit,
                "pricing_unit": pricing_unit,
                "standard_lot_size": 1000,
                "standard_lot_unit": lot_unit,
            },
        )

        today = date(2026, 10, 8)
        for i in range(30):
            obs_date = today - timedelta(days=35 - i)
            price = 70.0 + (i * 0.25)
            MarketPriceObservation.objects.get_or_create(
                commodity=commodity,
                observation_date=obs_date,
                is_prompt=True,
                defaults={
                    "open_price": price - 0.2,
                    "high_price": price + 0.5,
                    "low_price": price - 0.5,
                    "close_price": price,
                    "settlement_price": price,
                    "volume": 120000 + (i * 1000),
                    "open_interest": 1800000,
                },
            )
        return commodity

    def test_end_to_end_pipeline_and_llm_formatter(self):
        """Tests database extraction pipeline and LLM output formatting."""
        self._setup_test_commodity("CL")

        pipeline = FeaturePipeline()
        package = pipeline.extract_features("CL")

        assert package.instrument == "CL"
        assert package.price.last > 0

        # LLM JSON formatting
        json_str = format_llm_json(package)
        assert '"instrument": "CL"' in json_str
        assert '"trend":' in json_str
        assert '"momentum":' in json_str
        assert '"scores":' in json_str

        # LLM Prompt context formatting
        prompt_txt = format_llm_prompt_context(package)
        assert f"### QUANTITATIVE STATE: {package.name} (CL)" in prompt_txt
        assert "#### 1. Price & Multi-Horizon Returns" in prompt_txt
        assert "#### 2. Trend & Momentum" in prompt_txt
        assert "#### 6. Multi-Factor Quant Ratings" in prompt_txt

    def test_rest_api_endpoint(self):
        """Tests GET /api/quant/live-features/ endpoint."""
        self._setup_test_commodity("CL")
        client = APIClient()

        # JSON format
        resp = client.get("/api/quant/live-features/?commodity=CL")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["instrument"] == "CL"
        assert "price" in data
        assert "trend" in data
        assert "momentum" in data
        assert "volatility" in data
        assert "volume" in data
        assert "structure" in data
        assert "scores" in data

        # Prompt format
        resp_prompt = client.get("/api/quant/live-features/?commodity=CL&output=prompt")
        assert resp_prompt.status_code == status.HTTP_200_OK
        data_p = resp_prompt.json()
        assert data_p["status"] == "ok"
        assert data_p["format"] == "prompt"
        assert "prompt_context" in data_p
        assert "QUANTITATIVE STATE" in data_p["prompt_context"]

        # 404 for invalid commodity
        resp_404 = client.get("/api/quant/live-features/?commodity=NON_EXISTENT_TICKER")
        assert resp_404.status_code == status.HTTP_404_NOT_FOUND

