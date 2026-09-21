"""
Comprehensive test suite for Product / Instrument / Contract Master.
Tests contract specifications, month codes, institutional expiry calculation arithmetic,
pluggable providers, and REST API endpoints.
"""

from datetime import date as dt_date
from decimal import Decimal
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.contracts.models import (
    ContractSpecification,
    ContractExpiry,
    InstrumentType,
    ExpiryRuleType,
    SettlementMethod,
    MonthCode,
    MONTH_NUMBER_TO_CODE,
    CODE_TO_MONTH_NUMBER,
)
from apps.contracts.providers.base import BaseContractSpecProvider
from apps.contracts.providers.factory import get_contract_provider
from apps.contracts.services.expiry_service import (
    ContractExpiryService,
    month_to_code,
    code_to_month,
    generate_contract_symbol,
)
from apps.exchanges.models import ExchangeMaster


@pytest.fixture(scope="module")
def django_db_setup(django_db_setup, django_db_blocker):
    """Seed prerequisite metadata, exchanges, commodities, and contracts for testing."""
    with django_db_blocker.unblock():
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")
        call_command("seed_contracts")


@pytest.mark.django_db
def test_seed_contracts_command_and_idempotency():
    """Verify seeder creates contract specifications and prompt delivery expiries idempotently."""
    initial_specs = ContractSpecification.objects.count()
    initial_expiries = ContractExpiry.objects.count()

    assert initial_specs >= 20
    assert initial_expiries >= 150

    # Run again to ensure strict idempotency (no duplicate entries)
    call_command("seed_contracts")
    assert ContractSpecification.objects.count() == initial_specs
    assert ContractExpiry.objects.count() == initial_expiries


@pytest.mark.django_db
def test_contract_specification_model_relationships():
    """Verify physical specifications, units, exchange relationships, and tick values."""
    cl = ContractSpecification.objects.get(symbol_root="CL", exchange__mic="XNYM")
    assert cl.name == "Light Sweet Crude Oil (WTI) Futures"
    assert cl.commodity.code == "CL"
    assert cl.exchange.mic == "XNYM"
    assert cl.instrument_type == InstrumentType.FUTURES
    assert cl.contract_size == Decimal("1000.0")
    assert cl.contract_unit.code == "BBL"
    assert cl.price_quote_unit.code == "USD_BBL"
    assert cl.minimum_tick_size == Decimal("0.01")
    assert cl.tick_value == Decimal("10.00")
    assert cl.settlement_method == SettlementMethod.PHYSICAL
    assert cl.trading_months == "ALL_12"
    assert len(cl.trading_month_codes) == 12
    assert cl.expiries.count() == 12

    # Brent cash-settled check
    brent = ContractSpecification.objects.get(symbol_root="B", exchange__mic="IFEU")
    assert brent.settlement_method == SettlementMethod.CASH
    assert brent.expiry_rule == ExpiryRuleType.LAST_BUSINESS_DAY_OF_TWO_MONTHS_PRIOR

    # Corn seasonal cycle check
    corn = ContractSpecification.objects.get(symbol_root="ZC", exchange__mic="XCBT")
    assert corn.trading_month_codes == ["H", "K", "N", "U", "Z"]
    assert corn.contract_unit.code == "BU"
    assert corn.contract_size == Decimal("5000.0")


def test_month_code_and_symbol_conversions():
    """Test standard commodity month letter codes (F-Z) and symbol generation."""
    assert month_to_code(1) == "F"
    assert month_to_code(2) == "G"
    assert month_to_code(3) == "H"
    assert month_to_code(4) == "J"
    assert month_to_code(5) == "K"
    assert month_to_code(6) == "M"
    assert month_to_code(7) == "N"
    assert month_to_code(8) == "Q"
    assert month_to_code(9) == "U"
    assert month_to_code(10) == "V"
    assert month_to_code(11) == "X"
    assert month_to_code(12) == "Z"

    assert code_to_month("F") == 1
    assert code_to_month("z") == 12
    assert code_to_month("H") == 3

    with pytest.raises(ValueError):
        month_to_code(13)

    with pytest.raises(ValueError):
        code_to_month("A")

    # Symbol ticker formatting
    assert generate_contract_symbol("CL", 2026, 12) == "CLZ26"
    assert generate_contract_symbol("ZC", 2027, 3) == "ZCH27"
    assert generate_contract_symbol("B", 2026, 1) == "BF26"


@pytest.mark.django_db
def test_expiry_calendar_calculation_logic():
    """Verify deterministic expiry calculations across rule types."""
    cl = ContractSpecification.objects.get(symbol_root="CL", exchange__mic="XNYM")
    # Rule: 25th calendar day of prior month (with bus offset)
    # For December 2026 (CLZ26): prior month is November 2026.
    # Nov 25, 2026 is Wednesday (weekday 2). It's a trading day.
    ltd_cl = ContractExpiryService.calculate_last_trading_day(cl, 2026, 12)
    assert ltd_cl == dt_date(2026, 11, 25)

    # For November 2026 (CLX26): prior month is October 2026.
    # Oct 25, 2026 is Sunday (weekday 6). Non-trading day!
    # Offset by 3 trading days backward: Sunday 25 -> Fri 23 (1), Thu 22 (2), Wed 21 (3)
    ltd_clx = ContractExpiryService.calculate_last_trading_day(cl, 2026, 11)
    assert ltd_clx == dt_date(2026, 10, 21)
    assert ltd_clx.weekday() < 5  # Must be a weekday

    # Corn CBOT: business day preceding the 15th calendar day of contract month
    zc = ContractSpecification.objects.get(symbol_root="ZC", exchange__mic="XCBT")
    # March 2027: March 15 is Monday. Preceding trading day is Friday, March 12, 2027.
    ltd_zc = ContractExpiryService.calculate_last_trading_day(zc, 2027, 3)
    assert ltd_zc == dt_date(2027, 3, 12)
    assert ltd_zc.weekday() == 4  # Friday

    # LME Copper: Third Wednesday of the delivery month
    ca = ContractSpecification.objects.get(symbol_root="CA", exchange__mic="XLME")
    # July 2027: July 1 is Thursday. 1st Wed is July 7, 2nd Wed is July 14, 3rd Wed is July 21.
    ltd_ca = ContractExpiryService.calculate_last_trading_day(ca, 2027, 7)
    assert ltd_ca == dt_date(2027, 7, 21)
    assert ltd_ca.weekday() == 2  # Wednesday


@pytest.mark.django_db
def test_contract_api_endpoints_and_filters():
    """Verify REST API endpoints for specifications, forward expiries, and summary."""
    client = APIClient()

    # 1. List specifications
    resp = client.get("/api/contracts/specifications/")
    assert resp.status_code == 200
    data = resp.json()
    specs = data["results"] if isinstance(data, dict) and "results" in data else data
    assert len(specs) >= 20

    # 2. Filter by commodity
    resp_cl = client.get("/api/contracts/specifications/?commodity=CL")
    assert resp_cl.status_code == 200
    cl_data = resp_cl.json()
    cl_specs = cl_data["results"] if isinstance(cl_data, dict) and "results" in cl_data else cl_data
    assert len(cl_specs) >= 1
    assert all(item["commodity_code"] == "CL" for item in cl_specs)

    # 3. Filter by exchange
    resp_nymex = client.get("/api/contracts/specifications/?exchange=NYMEX")
    assert resp_nymex.status_code == 200
    nymex_data = resp_nymex.json()
    nymex_specs = nymex_data["results"] if isinstance(nymex_data, dict) and "results" in nymex_data else nymex_data
    assert len(nymex_specs) >= 1
    assert all(item["exchange_code"] == "NYMEX" for item in nymex_specs)

    # 4. Filter by settlement method
    resp_cash = client.get("/api/contracts/specifications/?settlement_method=CASH")
    assert resp_cash.status_code == 200
    cash_data = resp_cash.json()
    cash_specs = cash_data["results"] if isinstance(cash_data, dict) and "results" in cash_data else cash_data
    assert len(cash_specs) >= 1
    assert all(item["settlement_method"] == "CASH" for item in cash_specs)

    # 5. Detail specification with nested expiries
    resp_detail = client.get("/api/contracts/specifications/CL/")
    assert resp_detail.status_code == 200
    spec_data = resp_detail.json()
    assert spec_data["symbol_root"] == "CL"
    assert len(spec_data["expiries"]) == 12

    # 6. List forward expiries
    resp_exp = client.get("/api/contracts/expiries/?symbol_root=CL&year=2026")
    assert resp_exp.status_code == 200
    exp_data = resp_exp.json()
    exp_list = exp_data["results"] if isinstance(exp_data, dict) and "results" in exp_data else exp_data
    assert len(exp_list) > 0

    # 7. Single delivery contract lookup
    resp_clz = client.get("/api/contracts/expiries/CLZ26/")
    assert resp_clz.status_code == 200
    clz_data = resp_clz.json()
    assert clz_data["contract_symbol"] == "CLZ26"
    assert clz_data["contract_year"] == 2026
    assert clz_data["contract_month_code"] == "Z"
    assert clz_data["last_trading_day"] == "2026-11-25"

    # 8. Summary statistics
    resp_summary = client.get("/api/contracts/summary/")
    assert resp_summary.status_code == 200
    sum_data = resp_summary.json()
    assert sum_data["total_specifications"] >= 20
    assert sum_data["total_expiries"] >= 150
    assert "PHYSICAL" in sum_data["settlement_method_breakdown"]
    assert "CASH" in sum_data["settlement_method_breakdown"]


def test_pluggable_contract_provider_interface():
    """Verify that the contract provider conforms to BaseContractSpecProvider."""
    provider = get_contract_provider()
    assert isinstance(provider, BaseContractSpecProvider)

    specs = provider.get_specifications()
    assert len(specs) >= 20

    cl_spec = provider.get_specification("CL", "XNYM")
    assert cl_spec is not None
    assert cl_spec.symbol_root == "CL"
    assert cl_spec.contract_size == Decimal("1000.0")

    assert provider.get_specification("INVALID_ROOT_999", "XNYM") is None
