"""
Automated Test Suite for the 40-Method Institutional Seasonality Engine & Matrix.
Validates mathematical calculations, catalog specifications, REST API, and dashboard integration.
"""
import datetime
import numpy as np
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.test import RequestFactory

from apps.commodities.models import CommodityMaster, CommoditySector
from apps.exchanges.models import ExchangeMaster
from apps.metadata.models import UnitMaster, UnitType
from apps.market_data.models import MarketPriceObservation
from apps.dashboard.views import index
from apps.quant_engine.core.seasonality_methods import (
    SEASONALITY_40_CATALOG,
    evaluate_40_seasonality_methods,
)


@pytest.fixture
def setup_commodity(db):
    unit, _ = UnitMaster.objects.get_or_create(
        code="USD_TEST",
        defaults={"name": "US Dollar Test", "symbol": "$", "unit_type": UnitType.CURRENCY},
    )
    lot_unit, _ = UnitMaster.objects.get_or_create(
        code="BBL_TEST",
        defaults={"name": "Barrels Test", "symbol": "bbl", "unit_type": UnitType.VOLUME},
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
        code="CL",
        defaults={
            "name": "Crude Oil WTI",
            "sector": CommoditySector.ENERGY,
            "group": "CRUDE_OIL",
            "primary_exchange": exchange,
            "base_unit": lot_unit,
            "pricing_unit": unit,
            "standard_lot_size": 1000,
            "standard_lot_unit": lot_unit,
        },
    )
    # Seed 30 prompt price observations
    for i in range(30):
        d = datetime.date(2026, 1, 1) + datetime.timedelta(days=i)
        p = 75.0 + i * 0.15
        MarketPriceObservation.objects.get_or_create(
            commodity=commodity,
            observation_date=d,
            defaults={
                "is_prompt": True,
                "open_price": p - 0.2,
                "high_price": p + 0.8,
                "low_price": p - 0.6,
                "close_price": p,
                "settlement_price": p,
                "volume": 50000,
                "open_interest": 200000,
            },
        )
    return commodity


@pytest.mark.django_db
class TestSeasonality40Catalog:
    """
    Validates completeness and integrity of the 40-Method Seasonality Catalog.
    """

    def test_catalog_has_exactly_40_methods(self):
        assert len(SEASONALITY_40_CATALOG) == 40, f"Expected 40 methods, found {len(SEASONALITY_40_CATALOG)}"

    def test_catalog_numbering_is_sequential_1_to_40(self):
        numbers = [m["number"] for m in SEASONALITY_40_CATALOG]
        assert numbers == list(range(1, 41)), "Method numbering must be sequentially 1 to 40"

    def test_catalog_has_all_required_sections(self):
        sections = {m["section"] for m in SEASONALITY_40_CATALOG}
        expected_sections = {
            "Calendar",
            "Price/Return",
            "Volatility",
            "Intraday",
            "Volume/Liquidity",
            "Futures Curve",
            "Fundamentals",
            "Events",
            "Statistical",
            "Dynamic",
            "Regime",
            "Cross-market",
            "Trading",
            "Visualization",
        }
        assert sections == expected_sections, f"Missing or unexpected sections: {expected_sections.symmetric_difference(sections)}"

    def test_catalog_field_completeness(self):
        for m in SEASONALITY_40_CATALOG:
            assert m["number"] >= 1
            assert bool(m["section"])
            assert bool(m["name"])
            assert bool(m["why_it_matters"])
            assert bool(m["formula_summary"])
            assert bool(m["metric_type"])
            assert bool(m["icon"])


@pytest.mark.django_db
class TestSeasonality40EngineEvaluation:
    """
    Validates deterministic evaluation of the 40 seasonality methods.
    """

    @pytest.fixture
    def synthetic_market_series(self):
        start_date = datetime.date(2005, 1, 3)
        dates = []
        prices = []
        p = 60.0
        np.random.seed(42)

        for i in range(5000):
            d = start_date + datetime.timedelta(days=i)
            if d.weekday() < 5:
                # Add mild seasonal drift
                drift = 0.05 * np.sin(2 * np.pi * d.timetuple().tm_yday / 365.25)
                ret = drift + np.random.normal(0, 0.015)
                p = max(5.0, p * (1.0 + ret))
                dates.append(d)
                prices.append(p)

        return dates, np.array(prices)

    def test_evaluate_40_methods_output_structure(self, synthetic_market_series):
        dates, prices = synthetic_market_series
        current_date = dates[-1]

        res = evaluate_40_seasonality_methods(
            dates=dates,
            prices=prices,
            current_date=current_date,
            commodity_code="CL",
        )

        assert res["commodity"] == "CL"
        assert res["as_of"] == current_date
        assert res["total_methods"] == 40
        assert len(res["methods"]) == 40
        assert len(res["sections"]) == 14

        # Validate each evaluated method
        for m in res["methods"]:
            assert "number" in m
            assert "section" in m
            assert "name" in m
            assert "why_it_matters" in m
            assert "headline_metric" in m
            assert "headline_label" in m
            assert "status" in m
            assert "parameters" in m
            assert isinstance(m["parameters"], dict)

    def test_specific_method_computations(self, synthetic_market_series):
        dates, prices = synthetic_market_series
        current_date = dates[-1]

        res = evaluate_40_seasonality_methods(
            dates=dates,
            prices=prices,
            current_date=current_date,
            commodity_code="CL",
        )
        methods_map = {m["number"]: m for m in res["methods"]}

        # Method 2: Day-of-week seasonality
        m2 = methods_map[2]
        assert m2["name"] == "Day-of-week seasonality"
        assert "dow_stats" in m2["parameters"]
        assert len(m2["parameters"]["dow_stats"]) == 5

        # Method 8: Range / ATR seasonality
        m8 = methods_map[8]
        assert m8["name"] == "Range/ATR seasonality"
        assert "atr_20d" in m8["parameters"]
        assert m8["parameters"]["atr_20d"] > 0

        # Method 25: Autocorrelation-based seasonality
        m25 = methods_map[25]
        assert m25["name"] == "Autocorrelation-based seasonality"
        assert "acf_lags" in m25["parameters"]
        assert "lag_21" in m25["parameters"]["acf_lags"]

        # Method 27: Seasonal stability / strength
        m27 = methods_map[27]
        assert m27["name"] == "Seasonal stability/strength"
        assert -1.0 <= m27["parameters"]["stability_score"] <= 1.0

        # Method 33: Seasonal strategy backtest
        m33 = methods_map[33]
        assert m33["name"] == "Seasonal strategy backtest"
        assert "win_rate_pct" in m33["parameters"]
        assert "profit_factor" in m33["parameters"]

        # Method 36: Walk-forward / out-of-sample testing
        m36 = methods_map[36]
        assert m36["name"] == "Walk-forward/out-of-sample testing"
        assert "out_of_sample_return_pct" in m36["parameters"]

    def test_graceful_fallback_on_insufficient_data(self):
        # Empty inputs should not raise an unhandled exception
        res = evaluate_40_seasonality_methods(
            dates=[],
            prices=np.array([]),
            current_date=datetime.date(2026, 9, 30),
            commodity_code="NG",
        )
        assert res["total_methods"] == 40
        assert len(res["methods"]) == 40
        for m in res["methods"]:
            assert m["headline_metric"] is not None


@pytest.mark.django_db
class TestSeasonality40RestApi:
    """
    Validates REST API endpoint for the 40-Method Seasonality Matrix.
    """

    def test_get_seasonality_methods_success(self, client, setup_commodity):
        response = client.get("/api/quant/seasonality/methods/?commodity=CL")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["commodity"] == "CL"
        assert data["total_methods"] == 40
        assert len(data["methods"]) == 40
        assert len(data["sections"]) == 14
        assert "analytical_payloads" in data

    def test_get_seasonality_methods_unknown_commodity(self, client):
        response = client.get("/api/quant/seasonality/methods/?commodity=UNKNOWN_XYZ")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestSeasonality40DashboardIntegration:
    """
    Validates that the Institutional Terminal dashboard displays the 40 methods properly.
    """

    def test_dashboard_renders_40_seasonality_methods(self, setup_commodity):
        factory = RequestFactory()
        request = factory.get("/?commodity=CL")
        response = index(request)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Check section title (rewritten title & backwards compatibility)
        assert "Quantitative Seasonality Engine & Empirical Matrix" in content
        assert "40-Method Institutional Seasonality Matrix & Inspector" in content
        # Check presence of several key methods in HTML
        assert "Month-of-year seasonality" in content
        assert "Day-of-week seasonality" in content
        assert "Curve-shape / contango-backwardation seasonality" in content
        assert "Seasonal stability/strength" in content
        assert "Walk-forward/out-of-sample testing" in content
        # Check inspector modal presence
        assert "s40ModalBackdrop" in content
        # Check actual visual workbench container and controls
        assert "seasonalityWorkbench" in content
        assert "wbMethodSelect" in content
        assert "workbenchSvgChart" in content
        assert "wbDataTable" in content
        assert "wbKpisGrid" in content

    def test_all_40_methods_have_visualizations(self, setup_commodity):
        dates = [datetime.date(2026, 1, 1) + datetime.timedelta(days=i) for i in range(150)]
        prices = np.array([70.0 + np.sin(i / 10.0) * 8.0 for i in range(150)])
        current_date = datetime.date(2026, 5, 30)

        res = evaluate_40_seasonality_methods(
            dates=dates,
            prices=prices,
            current_date=current_date,
            commodity_code="CL",
        )

        assert len(res["methods"]) == 40
        for m in res["methods"]:
            assert "visualization" in m, f"Method {m['number']} missing visualization"
            viz = m["visualization"]
            assert "chart_type" in viz, f"Method {m['number']} missing chart_type"
            assert "y_axis_label" in viz, f"Method {m['number']} missing y_axis_label"
            assert "x_labels" in viz, f"Method {m['number']} missing x_labels"
            assert len(viz["x_labels"]) > 0, f"Method {m['number']} has empty x_labels"
            assert "series" in viz, f"Method {m['number']} missing series"
            assert len(viz["series"]) > 0, f"Method {m['number']} has empty series"
            assert "table_headers" in viz, f"Method {m['number']} missing table_headers"
            assert "table_rows" in viz, f"Method {m['number']} missing table_rows"
            assert len(viz["table_rows"]) > 0, f"Method {m['number']} has empty table_rows"
            assert "kpis" in viz, f"Method {m['number']} missing kpis"
            assert len(viz["kpis"]) > 0, f"Method {m['number']} has empty kpis"
            assert "institutional_takeaway" in viz, f"Method {m['number']} missing institutional_takeaway"
            assert len(viz["institutional_takeaway"]) > 10, f"Method {m['number']} takeaway too short"

