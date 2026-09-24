"""
Comprehensive test suite for Phase 10: Market Data & Time-Series Observation Store.

Covers:
- MarketPriceObservation, FundamentalObservation, CommitmentOfTradersObservation models.
- Point-in-time correctness (Section 7) & Rule 5 native SQL NULL handling for unobserved metrics.
- Computed quantitative properties (COT Managed Money Net, Commercial Net, % of Open Interest).
- Pluggable provider architecture (BaseMarketDataProvider, StaticMarketDataProvider, factory & registries).
- Management command (ingest_market_data) idempotency and filtering options.
- REST API list, retrieve, date range filtering, and telemetry summary.
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import pytest
from django.core.management import call_command
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.commodities.models import CommodityMaster
from apps.core.models import DataQualityStatus
from apps.market_data.models import (
    MarketPriceObservation,
    FundamentalObservation,
    CommitmentOfTradersObservation,
    COTReportType,
)
from apps.market_data.providers.base import (
    BaseMarketDataProvider,
    RawPriceObservation,
)
from apps.market_data.providers.factory import (
    get_market_data_provider,
    get_fundamental_provider,
    get_cot_provider,
    register_market_data_provider,
)
from apps.market_data.providers.static_data import (
    StaticMarketDataProvider,
    StaticFundamentalProvider,
    StaticCOTProvider,
)
from apps.metadata.models import UnitMaster
from apps.variables.models import VariableMaster


@pytest.mark.django_db
class TestMarketDataModels:
    """Unit tests for Market Data models, Point-in-Time timestamps, and Rule 5 NULL handling."""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")
        call_command("seed_contracts")
        call_command("seed_datasets")
        call_command("seed_variables")
        self.cl = CommodityMaster.objects.get(code="CL")
        self.brent = CommodityMaster.objects.get(code="BRENT")
        self.cushing_var = VariableMaster.objects.get(code="CRUDE_CUSHING_STOCKS")
        self.mbbl = UnitMaster.objects.get(code="MBBL")

    def test_market_price_observation_creation_and_properties(self):
        pub_time = datetime(2026, 9, 23, 20, 30, tzinfo=timezone.utc)
        obs = MarketPriceObservation.objects.create(
            commodity=self.cl,
            delivery_month="2026-11",
            is_prompt=True,
            observation_date=date(2026, 9, 23),
            open_price=Decimal("75.20"),
            high_price=Decimal("76.40"),
            low_price=Decimal("74.80"),
            close_price=Decimal("75.90"),
            settlement_price=Decimal("75.85"),
            volume=342000,
            open_interest=1820000,
            publication_time=pub_time,
            quality_status=DataQualityStatus.VALID,
        )

        assert obs.id is not None
        assert obs.price == Decimal("75.85")
        assert obs.is_available is True
        assert "75.85" in obs.display_settlement
        assert obs.ingestion_time is not None
        assert obs.publication_time == pub_time
        assert "CL" in str(obs)

    def test_market_price_unobserved_metrics_rule_5(self):
        """Unobserved prices must store SQL native NULL, not placeholder string or zero."""
        obs = MarketPriceObservation.objects.create(
            commodity=self.cl,
            delivery_month="2026-11",
            is_prompt=True,
            observation_date=date(2026, 9, 22),
            settlement_price=None,
            close_price=None,
        )
        assert obs.settlement_price is None
        assert obs.price is None
        assert obs.is_available is False
        assert obs.display_settlement == "NOT_AVAILABLE"

    def test_fundamental_observation_rule_5_and_properties(self):
        # Observed point
        obs_valid = FundamentalObservation.objects.create(
            variable=self.cushing_var,
            observation_date=date(2026, 9, 18),
            value=Decimal("24500.50"),
            unit=self.mbbl,
            period_start=date(2026, 9, 12),
            period_end=date(2026, 9, 18),
            publication_time=datetime(2026, 9, 23, 14, 30, tzinfo=timezone.utc),
        )
        assert obs_valid.is_available is True
        assert "24500.5" in obs_valid.display_value
        assert "MBBL" in obs_valid.display_value

        # Unobserved point (Rule 5)
        obs_missing = FundamentalObservation.objects.create(
            variable=self.cushing_var,
            observation_date=date(2026, 9, 11),
            value=None,
            unit=self.mbbl,
        )
        assert obs_missing.is_available is False
        assert obs_missing.display_value == "NOT_AVAILABLE"

    def test_cot_observation_calculations(self):
        cot = CommitmentOfTradersObservation.objects.create(
            commodity=self.cl,
            observation_date=date(2026, 9, 22),
            report_type=COTReportType.DISAGGREGATED,
            open_interest=1850000,
            prod_merc_long=380000,
            prod_merc_short=540000,
            swap_long=180000,
            swap_short=220000,
            money_manager_long=240000,
            money_manager_short=85000,
            money_manager_spread=45000,
        )

        # Money Manager Net: 240,000 - 85,000 = +155,000
        assert cot.money_manager_net == 155000
        # Commercial Net: (380k + 180k) - (540k + 220k) = 560k - 760k = -200,000
        assert cot.commercial_net == -200000
        # Money Manager % of OI: (155,000 / 1,850,000) * 100 = 8.38%
        assert cot.money_manager_net_pct_oi == 8.38
        # Commercial % of OI: (-200,000 / 1,850,000) * 100 = -10.81%
        assert cot.commercial_net_pct_oi == -10.81

    def test_unique_constraint_enforcement(self):
        CommitmentOfTradersObservation.objects.create(
            commodity=self.cl,
            observation_date=date(2026, 9, 22),
            report_type=COTReportType.DISAGGREGATED,
            open_interest=1000,
        )
        with pytest.raises(IntegrityError):
            CommitmentOfTradersObservation.objects.create(
                commodity=self.cl,
                observation_date=date(2026, 9, 22),
                report_type=COTReportType.DISAGGREGATED,
                open_interest=2000,
            )


@pytest.mark.django_db
class TestPluggableProviders:
    """Unit tests for Strategy provider implementations and Factory resolution."""

    def test_static_market_data_provider_output(self):
        provider = StaticMarketDataProvider()
        assert provider.name == "Static Exchange Settlement Simulator"
        assert provider.is_healthy() is True

        start = date(2026, 9, 1)
        end = date(2026, 9, 10)
        observations = provider.fetch_price_observations("CL", start_date=start, end_date=end)

        assert len(observations) > 0
        for obs in observations:
            # Weekend filter check
            assert obs.observation_date.weekday() < 5
            assert obs.symbol == "CL"
            assert obs.settlement_price is not None
            assert obs.publication_time is not None

        # Check prompt vs term structure
        prompt_obs = [o for o in observations if o.is_prompt]
        m2_obs = [o for o in observations if o.contract_month == "2026-12"]
        assert len(prompt_obs) > 0
        assert len(m2_obs) > 0
        # Verify backwardation structure simulated
        assert m2_obs[0].settlement_price < prompt_obs[0].settlement_price

    def test_static_fundamental_provider_output(self):
        provider = StaticFundamentalProvider()
        assert provider.is_healthy() is True

        start = date(2026, 6, 1)
        end = date(2026, 9, 20)
        obs = provider.fetch_fundamental_observations("CRUDE_CUSHING_STOCKS", start, end)

        assert len(obs) > 0
        # Verify period_start, period_end, publication_time point-in-time timestamps
        first = obs[0]
        assert first.period_start < first.period_end
        assert first.publication_time.date() > first.period_end

    def test_static_cot_provider_output(self):
        provider = StaticCOTProvider()
        assert provider.is_healthy() is True

        start = date(2026, 7, 1)
        end = date(2026, 9, 20)
        obs = provider.fetch_cot_observations("CL", start, end)

        assert len(obs) > 0
        # Survey Tuesday, Publication Friday
        for item in obs:
            assert item.observation_date.weekday() == 1  # Tuesday
            assert item.publication_time.weekday() == 4  # Friday

    def test_provider_factory_resolution_and_registration(self):
        m_prov = get_market_data_provider()
        assert isinstance(m_prov, StaticMarketDataProvider)

        f_prov = get_fundamental_provider()
        assert isinstance(f_prov, StaticFundamentalProvider)

        c_prov = get_cot_provider()
        assert isinstance(c_prov, StaticCOTProvider)

        # Test registering a mock provider
        class MockProvider(BaseMarketDataProvider):
            @property
            def name(self):
                return "Mock Feed"

            def fetch_price_observations(self, symbol, start_date=None, end_date=None, **kwargs):
                return []

        register_market_data_provider("mock", MockProvider)
        mock_instance = get_market_data_provider("mock")
        assert isinstance(mock_instance, MockProvider)


@pytest.mark.django_db
class TestMarketDataIngestCommand:
    """Tests for the ingest_market_data management command."""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")
        call_command("seed_contracts")
        call_command("seed_providers")
        call_command("seed_datasets")
        call_command("seed_variables")
        call_command("seed_endpoints")

    def test_idempotent_ingestion(self):
        # Initial run
        call_command("ingest_market_data", "--clear", "--days=30")
        p_count_1 = MarketPriceObservation.objects.count()
        f_count_1 = FundamentalObservation.objects.count()
        c_count_1 = CommitmentOfTradersObservation.objects.count()

        assert p_count_1 > 0
        assert f_count_1 > 0
        assert c_count_1 > 0

        # Run again without clear (idempotency test)
        call_command("ingest_market_data", "--days=30")
        assert MarketPriceObservation.objects.count() == p_count_1
        assert FundamentalObservation.objects.count() == f_count_1
        assert CommitmentOfTradersObservation.objects.count() == c_count_1

    def test_type_and_commodity_filtering(self):
        call_command("ingest_market_data", "--clear", "--type=prices", "--commodity=CL", "--days=15")
        assert MarketPriceObservation.objects.filter(commodity__code="CL").exists()
        assert not MarketPriceObservation.objects.filter(commodity__code="BRENT").exists()
        assert FundamentalObservation.objects.count() == 0
        assert CommitmentOfTradersObservation.objects.count() == 0


@pytest.mark.django_db
class TestMarketDataAPI:
    """Tests for REST API endpoints under /api/market-data/."""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")
        call_command("seed_contracts")
        call_command("seed_providers")
        call_command("seed_datasets")
        call_command("seed_variables")
        call_command("seed_endpoints")
        call_command("ingest_market_data", "--clear", "--days=30")
        self.client = APIClient()

    def test_prices_list_and_filters(self):
        res = self.client.get("/api/market-data/prices/?commodity=CL&is_prompt=true")
        assert res.status_code == 200
        payload = res.json()
        data = payload["results"] if isinstance(payload, dict) and "results" in payload else payload
        assert len(data) > 0
        for item in data:
            assert item["commodity_code"] == "CL"
            assert item["is_prompt"] is True
            assert "price" in item
            assert "display_settlement" in item

    def test_price_detail_view(self):
        price_obj = MarketPriceObservation.objects.first()
        res = self.client.get(f"/api/market-data/prices/{price_obj.id}/")
        assert res.status_code == 200
        assert res.json()["id"] == str(price_obj.id)

    def test_fundamentals_list_and_filters(self):
        res = self.client.get("/api/market-data/fundamentals/?variable=CRUDE_CUSHING_STOCKS")
        assert res.status_code == 200
        payload = res.json()
        data = payload["results"] if isinstance(payload, dict) and "results" in payload else payload
        assert len(data) > 0
        assert data[0]["variable_code"] == "CRUDE_CUSHING_STOCKS"

    def test_cot_list_and_calculations(self):
        res = self.client.get("/api/market-data/cot/?commodity=CL")
        assert res.status_code == 200
        payload = res.json()
        data = payload["results"] if isinstance(payload, dict) and "results" in payload else payload
        assert len(data) > 0
        item = data[0]
        assert item["commodity_code"] == "CL"
        assert "money_manager_net" in item
        assert "commercial_net" in item
        assert "money_manager_net_pct_oi" in item

    def test_market_data_summary(self):
        res = self.client.get("/api/market-data/summary/")
        assert res.status_code == 200
        data = res.json()
        assert data["total_price_observations"] > 0
        assert data["total_fundamental_observations"] > 0
        assert data["total_cot_observations"] > 0
        assert data["covered_commodities_count"] >= 5
