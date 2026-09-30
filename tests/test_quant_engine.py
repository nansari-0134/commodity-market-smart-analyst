"""
Comprehensive Automated Test Suite for Quantitative Engine (Phase 11).

Tests:
1. Pure NumPy Market-State calculations (returns, Garman-Klass, ATR, RVOL, OI regimes).
2. Monotone PCHIP Spline interpolation & forward curve slope analytics.
3. Processing spreads (3:2:1 Crack, Soybean Crush, Spark Spread).
4. Vectorized Cross-Commodity correlation & Engle-Granger cointegration.
5. Seasonality envelopes, directional tenure patterns & forward 1M volatility.
6. Divergence detection & MAD-Z scores.
7. Pydantic v2 QuantitativeEvidencePackage validation.
8. REST API endpoints (/api/quant/...).
"""
import pytest
import numpy as np
from datetime import date, datetime, timezone
from rest_framework.test import APIClient

from apps.commodities.models import CommodityMaster, CommoditySector
from apps.exchanges.models import ExchangeMaster
from apps.metadata.models import UnitMaster, UnitType
from apps.market_data.models import MarketPriceObservation
from apps.quant_engine.core import (
    compute_returns,
    compute_realized_volatility,
    compute_garman_klass_volatility,
    compute_atr,
    compute_volume_metrics,
    classify_oi_regime,
    fit_forward_curve_spline,
    sample_forward_curve,
    analyze_curve_structure,
    compute_321_crack_spread,
    compute_soybean_crush_spread,
    compute_spark_spread,
    compute_all_pairs_correlation_matrix,
    run_engle_granger_cointegration,
    find_logical_complex_for_commodity,
    compute_macro_factor_sensitivities,
    compute_seasonal_envelopes,
    find_directional_tenure_patterns,
    compute_forward_volatility_expectation,
    compute_mad_zscore,
    detect_price_oi_divergence,
    detect_price_cot_divergence,
    detect_price_curve_divergence,
)
from apps.quant_engine.evidence.schema import QuantitativeEvidencePackage
from apps.quant_engine.services.evidence_builder import EvidencePackageBuilder
from apps.quant_engine.models import DiscoveryRegistry, EvidencePackageSnapshot


# -----------------------------------------------------------------------------
# 1. Market-State & Volatility Core Tests
# -----------------------------------------------------------------------------
def test_compute_returns():
    prices = np.array([100.0, 102.0, 101.0, 105.0, 110.0])
    rets = compute_returns(prices, horizons=(1, 2, 4))
    assert rets["returns_1d"] == pytest.approx((110.0 - 105.0) / 105.0, rel=1e-4)
    assert rets["returns_4d"] == pytest.approx((110.0 - 100.0) / 100.0, rel=1e-4)


def test_realized_volatility():
    # Constant price series has zero volatility
    prices = np.ones(50) * 100.0
    vol = compute_realized_volatility(prices, windows=(20,))
    assert vol["realized_vol_20d"] == 0.0

    # Series with standard variance
    np.random.seed(42)
    varying = 100.0 * np.exp(np.cumsum(np.random.normal(0, 0.01, 60)))
    vol = compute_realized_volatility(varying, windows=(20,))
    assert vol["realized_vol_20d"] > 0.0


def test_garman_klass_volatility():
    opens = np.array([100.0, 101.0, 102.0, 101.5])
    highs = np.array([102.0, 103.0, 103.5, 103.0])
    lows = np.array([99.0, 100.0, 101.0, 100.5])
    closes = np.array([101.0, 102.0, 101.5, 102.5])
    
    gk_vol = compute_garman_klass_volatility(opens, highs, lows, closes, window=4)
    assert gk_vol > 0.0


def test_atr_calculation():
    highs = np.array([102.0, 105.0, 104.0, 106.0])
    lows = np.array([99.0, 101.0, 100.0, 102.0])
    closes = np.array([101.0, 104.0, 102.0, 105.0])
    
    atr, atr_pct = compute_atr(highs, lows, closes, period=3)
    assert atr > 0.0
    assert atr_pct > 0.0


def test_volume_metrics():
    volumes = np.array([1000.0, 1200.0, 1100.0, 1500.0, 3000.0])
    rvol, z_score = compute_volume_metrics(volumes, window=4)
    assert rvol > 1.0  # Latest volume is 3000 vs mean ~1200
    assert z_score > 0.0


def test_oi_regime_classification():
    assert classify_oi_regime(0.01, 0.02) == "LONG_ACCUMULATION"
    assert classify_oi_regime(0.01, -0.02) == "SHORT_COVERING"
    assert classify_oi_regime(-0.01, 0.02) == "SHORT_ACCUMULATION"
    assert classify_oi_regime(-0.01, -0.02) == "LONG_LIQUIDATION"
    assert classify_oi_regime(0.0, 0.0) == "NEUTRAL"


# -----------------------------------------------------------------------------
# 2. Forward Curve & Spline Tests
# -----------------------------------------------------------------------------
def test_curve_structure_analytics():
    # Backwardation: prompt > forward
    back_res = analyze_curve_structure(m1_price=80.0, m2_price=78.0, m3_price=76.5, m12_price=70.0)
    assert back_res["prompt_spread"] == 2.0
    assert back_res["roll_yield_1y"] > 0
    assert "BACKWARDATION" in back_res["curve_state"]

    # Contango: prompt < forward
    cont_res = analyze_curve_structure(m1_price=70.0, m2_price=72.0, m3_price=73.5, m12_price=80.0)
    assert cont_res["prompt_spread"] == -2.0
    assert cont_res["roll_yield_1y"] < 0
    assert "CONTANGO" in cont_res["curve_state"]


def test_monotone_spline_interpolation():
    tenors = np.array([15, 45, 75, 105, 180, 360])
    # Monotonically declining curve (backwardation)
    prices = np.array([80.0, 78.5, 77.2, 76.0, 74.0, 70.0])
    
    spline = fit_forward_curve_spline(tenors, prices)
    sampled = sample_forward_curve(spline, target_tenors=(30, 60, 90, 180, 360))
    
    # Monotonicity check: 1M price must be between 15D and 45D price
    assert 78.5 <= sampled["1M"] <= 80.0
    assert 70.0 <= sampled["12M"] <= 74.0


# -----------------------------------------------------------------------------
# 3. Processing Spreads Tests
# -----------------------------------------------------------------------------
def test_crack_321_spread():
    # WTI = 80 $/bbl, Gasoline = $2.50/gal (105 $/bbl), Heating Oil = $2.80/gal (117.6 $/bbl)
    # Gasoline rev: 2 * (2.50 * 42) = 210
    # HO rev: 1 * (2.80 * 42) = 117.6
    # Crude cost: 3 * 80 = 240
    # Gross: 327.6 - 240 = 87.6 / 3 = 29.20 $/bbl
    crack = compute_321_crack_spread(wti_crude_bbl=80.0, rbob_gasoline_gal=2.50, heating_oil_gal=2.80)
    assert crack == pytest.approx(29.20, abs=0.05)

    # Test auto-conversion from cents/gallon
    crack_cents = compute_321_crack_spread(wti_crude_bbl=80.0, rbob_gasoline_gal=250.0, heating_oil_gal=280.0)
    assert crack_cents == crack


def test_soybean_crush_spread():
    # Beans = $12.00/bu, Meal = $350/ton, Oil = 48 cents/lb
    crush = compute_soybean_crush_spread(soybeans_bu=12.0, soybean_meal_ton=350.0, soybean_oil_lb=48.0)
    # Meal: 350 * 0.022 = 7.70, Oil: 48 * 0.11 = 5.28 -> Gross = 12.98 - 12.00 = 0.98 $/bu
    assert crush == pytest.approx(0.98, abs=0.05)


def test_spark_spread():
    # Power = $50/MWh, Gas = $3.50/MMBtu, Heat rate = 7000 Btu/kWh
    # Fuel cost = 3.50 * 7.0 = 24.50 -> Spark = 50 - 24.50 = 25.50
    spark = compute_spark_spread(power_price_mwh=50.0, natural_gas_mmbtu=3.50)
    assert spark == 25.50


# -----------------------------------------------------------------------------
# 4. Cross-Commodity & Cointegration Tests
# -----------------------------------------------------------------------------
def test_all_pairs_correlation_matrix():
    returns = np.array([
        [0.01, 0.012, -0.005],
        [0.02, 0.018, -0.010],
        [-0.01, -0.008, 0.005],
        [0.015, 0.014, -0.008],
        [-0.02, -0.019, 0.012],
    ])
    tickers = ["CL", "BRENT", "NG"]
    corr_dict = compute_all_pairs_correlation_matrix(returns, tickers)
    
    assert "CL-BRENT" in corr_dict
    assert corr_dict["CL-BRENT"] > 0.90  # CL and BRENT move tightly together
    assert "CL-NG" in corr_dict
    assert corr_dict["CL-NG"] < 0.0  # NG moves inversely in test data


def test_engle_granger_cointegration_core():
    # Generate stationary synthetic cointegrated pair: Y = 1.5 * X + stationary_noise
    np.random.seed(42)
    x = 100.0 + np.cumsum(np.random.normal(0, 1.0, 100))
    # Mean-reverting noise (AR(1) with phi=0.5)
    noise = np.zeros(100)
    for i in range(1, 100):
        noise[i] = 0.4 * noise[i - 1] + np.random.normal(0, 0.5)
    y = 1.5 * x + noise
    
    res = run_engle_granger_cointegration(y, x, "Y-X")
    assert res["hedge_ratio_beta"] == pytest.approx(1.5, abs=0.1)
    assert res["is_cointegrated"] is True
    assert res["half_life_days"] is not None
    assert res["half_life_days"] < 10.0


def test_logical_complex_lookup():
    cl_complex = find_logical_complex_for_commodity("CL")
    assert cl_complex["complex_key"] == "REFINERY_ENERGY_COMPLEX"
    assert "BRENT" in cl_complex["members"]
    assert "RB" in cl_complex["members"]

    zs_complex = find_logical_complex_for_commodity("ZS")
    assert zs_complex["complex_key"] == "OILSEED_CRUSH_COMPLEX"
    assert "ZM" in zs_complex["members"]


def test_macro_factor_sensitivities():
    comm_ret = np.array([0.01, 0.02, -0.01, 0.015, -0.02])
    macro_factors = {
        "DXY": np.array([-0.005, -0.010, 0.008, -0.007, 0.012]),
    }
    sens = compute_macro_factor_sensitivities(comm_ret, macro_factors, window=5)
    assert "dxy_corr_5d" in sens
    assert sens["dxy_corr_5d"] < -0.80  # Inverted macro relationship


# -----------------------------------------------------------------------------
# 5. Seasonality & Volatility Peak Tests
# -----------------------------------------------------------------------------
def test_seasonality_envelopes():
    dates = [date(2025, 1, i) for i in range(1, 31)] + [date(2026, 1, i) for i in range(1, 31)]
    prices = np.concatenate([np.linspace(70, 75, 30), np.linspace(72, 78, 30)])
    
    env = compute_seasonal_envelopes(dates, prices, date(2026, 1, 15), lookback_years=2)
    assert "day_of_year" in env
    assert "percentiles_5y" in env


def test_directional_tenure_patterns():
    # Synthetic 5-year data where January always rallies
    dates = []
    prices = []
    for yr in [2021, 2022, 2023, 2024, 2025]:
        for d in range(1, 250):
            # Month 1 (DOY 1 to 30) rallies from 100 to 110
            dates.append(date(yr, 1, min(d, 28)) if d <= 28 else date(yr, min(1 + d // 30, 12), min(1 + (d % 28), 28)))
            price = 100.0 + (d * 0.3) if d <= 30 else 109.0
            prices.append(price)
            
    pattern = find_directional_tenure_patterns(dates, np.array(prices), date(2025, 1, 5), forward_days=20)
    assert pattern["win_rate"] >= 0.65


def test_forward_volatility_expectation():
    dates = [date(2025, 1, min(i, 28)) for i in range(1, 200)] + [date(2026, 1, min(i, 28)) for i in range(1, 200)]
    prices = np.random.normal(80, 2, len(dates))
    
    vol_peak = compute_forward_volatility_expectation(dates, prices, date(2026, 6, 15), "ZC")
    assert "forward_expected_vol_30d" in vol_peak
    assert "Planting & Summer Weather Risk Market" in vol_peak["seasonal_catalyst"]


# -----------------------------------------------------------------------------
# 6. Divergence Detection Tests
# -----------------------------------------------------------------------------
def test_divergence_detection():
    # Price vs OI divergence: price up 6% while OI drops 6%
    p = np.linspace(100, 106, 25)
    oi = np.linspace(1000, 940, 25)
    div = detect_price_oi_divergence(p, oi, lookback=20)
    assert div is not None
    assert div["type"] == "PRICE_VS_OI_DIVERGENCE"

    # Price vs COT divergence
    div_cot = detect_price_cot_divergence(price_change_4w_pct=0.05, mm_net_change_contracts=-15000, commercial_net_change_contracts=12000)
    assert div_cot is not None
    assert div_cot["severity"] == "SEVERE"


# -----------------------------------------------------------------------------
# 7. End-to-End EvidencePackageBuilder & DB Fixture Test
# -----------------------------------------------------------------------------
@pytest.mark.django_db
def test_evidence_package_builder_and_rest_apis():
    unit, _ = UnitMaster.objects.get_or_create(
        code="USD_BBL",
        defaults={"name": "US Dollar per Barrel", "symbol": "USD_BBL", "unit_type": UnitType.PRICE_PER_UNIT},
    )
    lot_unit, _ = UnitMaster.objects.get_or_create(
        code="BBL",
        defaults={"name": "Barrels", "symbol": "BBL", "unit_type": UnitType.VOLUME},
    )
    
    exchange = ExchangeMaster.objects.filter(mic="XNYM").first() or ExchangeMaster.objects.filter(code="NYMEX").first()
    if not exchange:
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
    
    commodity = CommodityMaster.objects.filter(code="CL_TEST").first()
    if not commodity:
        commodity = CommodityMaster.objects.create(
            code="CL_TEST",
            name="WTI Crude Test",
            sector=CommoditySector.ENERGY,
            group="CRUDE_OIL",
            primary_exchange=exchange,
            base_unit=lot_unit,
            pricing_unit=unit,
            standard_lot_size=1000,
            standard_lot_unit=lot_unit,
        )
    
    # Create 40 historical prompt price observations
    base_price = 75.0
    for i in range(40):
        d = date(2026, 1, 1) + np.timedelta64(i, "D").astype("timedelta64[D]").item()
        p = base_price + (i * 0.1)
        MarketPriceObservation.objects.create(
            commodity=commodity,
            observation_date=d,
            is_prompt=True,
            open_price=p - 0.2,
            high_price=p + 0.8,
            low_price=p - 0.6,
            close_price=p,
            settlement_price=p,
            volume=50000 + i * 100,
            open_interest=200000 + i * 50,
        )
        
    # Execute EvidencePackageBuilder
    builder = EvidencePackageBuilder("CL_TEST")
    package = builder.build(persist_snapshot=True)
    
    # Verify Pydantic schema validation
    assert isinstance(package, QuantitativeEvidencePackage)
    assert package.market == "CL_TEST"
    assert package.market_state.spot_price > 75.0
    assert package.market_state.realized_vol_20d >= 0.0
    assert package.provenance.price_source == exchange.code
    
    # Verify persistence
    assert EvidencePackageSnapshot.objects.filter(commodity=commodity).exists()
    
    # Test REST API Views
    client = APIClient()
    
    # 1. Evidence package endpoint
    resp = client.get("/api/quant/evidence-package/?commodity=CL_TEST")
    assert resp.status_code == 200
    assert resp.data["market"] == "CL_TEST"
    assert "market_state" in resp.data
    assert "cross_commodity" in resp.data
    assert "seasonality" in resp.data
    
    # 2. Market state endpoint
    resp = client.get("/api/quant/market-state/?commodity=CL_TEST")
    assert resp.status_code == 200
    assert resp.data["commodity"] == "CL_TEST"
    
    # 3. Curve endpoint
    resp = client.get("/api/quant/curve/?commodity=CL_TEST")
    assert resp.status_code == 200
    assert "curve_state" in resp.data
    assert "contracts" in resp.data
    
    # 4. Spreads endpoint
    resp = client.get("/api/quant/spreads/?commodity=CL_TEST")
    assert resp.status_code == 200
    assert "spreads" in resp.data
    
    # 5. Cross-commodity endpoint
    resp = client.get("/api/quant/cross-commodity/?commodity=CL_TEST")
    assert resp.status_code == 200
    assert "cross_commodity" in resp.data
    
    # 6. Seasonality endpoint
    resp = client.get("/api/quant/seasonality/?commodity=CL_TEST")
    assert resp.status_code == 200
    assert "seasonality" in resp.data
    
    # 7. Discoveries list endpoint
    resp = client.get("/api/quant/discoveries/")
    assert resp.status_code == 200
