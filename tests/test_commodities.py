"""
Comprehensive test suite for Commodity Master, Deliverable Chemistry, and Multi-Exchange Listings.
"""
from decimal import Decimal
import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient
from apps.commodities.models import (
    CommodityMaster,
    CommodityExchangeListing,
    CommoditySector,
    SettlementMethod,
    LiquidityTier,
)
from apps.commodities.providers.factory import get_commodity_provider
from apps.commodities.providers.base import BaseCommodityCatalogProvider
from apps.exchanges.models import ExchangeMaster
from apps.metadata.models import UnitMaster


@pytest.fixture(scope="module")
def django_db_setup(django_db_setup, django_db_blocker):
    """Seed prerequisite metadata, exchanges, and commodities for testing."""
    with django_db_blocker.unblock():
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")


@pytest.mark.django_db
def test_seed_commodities_command_and_idempotency():
    """Verify seeder creates benchmark commodities and multi-exchange listings idempotently."""
    initial_commodities = CommodityMaster.objects.count()
    initial_listings = CommodityExchangeListing.objects.count()

    assert initial_commodities >= 20
    assert initial_listings >= 35

    # Run again to ensure strict idempotency (no duplicate entries)
    call_command("seed_commodities")
    assert CommodityMaster.objects.count() == initial_commodities
    assert CommodityExchangeListing.objects.count() == initial_listings


@pytest.mark.django_db
def test_commodity_model_validation_and_relationships():
    """Verify physical specifications, units, exchanges, and tick parameters."""
    wti = CommodityMaster.objects.get(code="CL")
    assert wti.name == "Light Sweet Crude Oil (WTI)"
    assert wti.sector == CommoditySector.ENERGY
    assert wti.group == "CRUDE_OIL"
    assert wti.primary_exchange.code == "NYMEX"
    assert wti.base_unit.code == "BBL"
    assert wti.pricing_unit.code == "USD_BBL"
    assert wti.standard_lot_size == Decimal("1000.0")
    assert wti.minimum_tick_size == Decimal("0.01")
    assert wti.tick_value == Decimal("10.00")
    assert wti.settlement_method == SettlementMethod.PHYSICAL
    assert "Cushing" in wti.primary_delivery_hub
    assert wti.quality_specifications["api_gravity_min"] == 37.0
    assert wti.quality_specifications["sulfur_pct_max"] == 0.42

    # Brent cash settlement against ICE Brent Index
    brent = CommodityMaster.objects.get(code="BRENT")
    assert brent.primary_exchange.code == "ICE_EU"
    assert brent.settlement_method == SettlementMethod.CASH
    assert brent.quality_specifications["cash_settlement_index"] == "ICE Brent Index"

    # Corn crop year and quality thresholds
    corn = CommodityMaster.objects.get(code="CORN")
    assert corn.primary_exchange.code == "CBOT"
    assert corn.crop_year_start_month == 9
    assert corn.quality_specifications["moisture_pct_max"] == 15.0
    assert corn.quality_specifications["test_weight_lbs_bu_min"] == 54.0


@pytest.mark.django_db
def test_multi_exchange_listings_structure():
    """Verify same physical commodity mapped to multiple active venues with volume & OI."""
    # Gold on COMEX (primary), MCX India, and SHFE Shanghai
    gold = CommodityMaster.objects.get(code="GOLD")
    listings = gold.exchange_listings.all()
    assert listings.count() >= 3

    comex_listing = listings.get(exchange__code="COMEX")
    assert comex_listing.ticker_symbol == "GC"
    assert comex_listing.is_primary_benchmark is True
    assert comex_listing.contract_size == Decimal("100.0")
    assert comex_listing.trading_currency == "USD"
    assert comex_listing.typical_daily_volume > 200000

    mcx_listing = listings.get(exchange__code="MCX")
    assert mcx_listing.ticker_symbol == "GOLD"
    assert mcx_listing.is_primary_benchmark is False
    assert mcx_listing.trading_currency == "INR"
    assert mcx_listing.typical_daily_volume > 10000

    shfe_listing = listings.get(exchange__code="SHFE")
    assert shfe_listing.ticker_symbol == "AU"
    assert shfe_listing.trading_currency == "CNY"

    # Verify WTI listing on MCX is CASH settled based on NYMEX settlement
    wti = CommodityMaster.objects.get(code="CL")
    wti_mcx = wti.exchange_listings.get(exchange__code="MCX")
    assert wti_mcx.settlement_method == SettlementMethod.CASH
    assert wti_mcx.trading_currency == "INR"


@pytest.mark.django_db
def test_commodity_api_list_and_filters():
    """Test REST API list view and multi-dimensional query filters."""
    client = APIClient()
    url = reverse("commodities:commodity_list")

    # Full list
    res = client.get(url)
    assert res.status_code == 200
    items = res.data["results"] if isinstance(res.data, dict) and "results" in res.data else res.data
    assert len(items) >= 20

    # Filter by sector
    res_energy = client.get(f"{url}?sector=ENERGY")
    assert res_energy.status_code == 200
    items_energy = res_energy.data["results"] if isinstance(res_energy.data, dict) and "results" in res_energy.data else res_energy.data
    assert len(items_energy) >= 4
    for c in items_energy:
        assert c["sector"] == "ENERGY"

    # Filter by settlement method
    res_cash = client.get(f"{url}?settlement=CASH")
    assert res_cash.status_code == 200
    items_cash = res_cash.data["results"] if isinstance(res_cash.data, dict) and "results" in res_cash.data else res_cash.data
    assert len(items_cash) >= 2
    for c in items_cash:
        assert c["settlement_method"] == "CASH"

    # Filter by exchange listing (commodities trading on MCX India)
    res_mcx = client.get(f"{url}?exchange=MCX")
    assert res_mcx.status_code == 200
    items_mcx = res_mcx.data["results"] if isinstance(res_mcx.data, dict) and "results" in res_mcx.data else res_mcx.data
    mcx_codes = [c["code"] for c in items_mcx]
    assert "CL" in mcx_codes
    assert "GOLD" in mcx_codes
    assert "COPPER" in mcx_codes

    # Search filter
    res_search = client.get(f"{url}?search=wti")
    assert res_search.status_code == 200
    items_search = res_search.data["results"] if isinstance(res_search.data, dict) and "results" in res_search.data else res_search.data
    assert any(c["code"] == "CL" for c in items_search)


@pytest.mark.django_db
def test_commodity_api_detail_endpoints():
    """Test detail view by code and UUID, plus listings sub-endpoint."""
    client = APIClient()

    # Detail by code
    url_code = reverse("commodities:commodity_detail", kwargs={"identifier": "CL"})
    res = client.get(url_code)
    assert res.status_code == 200
    assert res.data["code"] == "CL"
    assert res.data["primary_exchange_code"] == "NYMEX"
    assert "quality_specifications" in res.data
    assert len(res.data["exchange_listings"]) >= 2

    # Detail by UUID
    wti = CommodityMaster.objects.get(code="CL")
    url_uuid = reverse("commodities:commodity_detail", kwargs={"identifier": str(wti.id)})
    res_uuid = client.get(url_uuid)
    assert res_uuid.status_code == 200
    assert res_uuid.data["code"] == "CL"

    # Non-existent commodity returns 404
    res_404 = client.get(reverse("commodities:commodity_detail", kwargs={"identifier": "UNKNOWN_XYZ"}))
    assert res_404.status_code == 404

    # Listings sub-endpoint
    url_listings = reverse("commodities:commodity_listings", kwargs={"identifier": "CL"})
    res_listings = client.get(url_listings)
    assert res_listings.status_code == 200
    assert res_listings.data["commodity_code"] == "CL"
    assert len(res_listings.data["listings"]) >= 2


@pytest.mark.django_db
def test_commodity_summary_and_sectors_apis():
    """Test summary statistics and sectors endpoints."""
    client = APIClient()

    # Summary API
    url_sum = reverse("commodities:commodity_summary")
    res_sum = client.get(url_sum)
    assert res_sum.status_code == 200
    assert res_sum.data["total_commodities"] >= 20
    assert res_sum.data["total_exchange_listings"] >= 35
    assert "ENERGY" in res_sum.data["sectors"]
    assert "PHYSICAL" in res_sum.data["settlement_methods"]
    assert len(res_sum.data["venues"]) >= 5

    # Sectors API
    url_sec = reverse("commodities:commodity_sectors")
    res_sec = client.get(url_sec)
    assert res_sec.status_code == 200
    sector_codes = [s["code"] for s in res_sec.data["sectors"]]
    assert "ENERGY" in sector_codes
    assert "AGRICULTURE" in sector_codes
    assert "METALS_BASE" in sector_codes
    assert "METALS_PRECIOUS" in sector_codes


def test_pluggable_catalog_provider_interface():
    """Verify that catalog provider conforms to BaseCommodityCatalogProvider contract."""
    provider = get_commodity_provider()
    assert isinstance(provider, BaseCommodityCatalogProvider)

    commodities = provider.get_commodities()
    assert len(commodities) >= 20

    cl_spec = provider.get_commodity("CL")
    assert cl_spec is not None
    assert cl_spec.code == "CL"
    assert cl_spec.primary_exchange_code == "NYMEX"
    assert len(cl_spec.listings) >= 2

    assert provider.get_commodity("INVALID_CODE_123") is None
