"""
Automated unit and API tests for Phase 3: Exchange Master.
"""
from datetime import date as dt_date
import pytest
from django.urls import reverse
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient
from apps.exchanges.models import (
    ExchangeMaster,
    ExchangeTier,
    ExchangeTradingSession,
    ExchangeHoliday,
    SessionType,
)
from apps.exchanges.services.holiday_service import ExchangeHolidaySyncService


@pytest.mark.django_db
def test_exchange_model_validation():
    """Verify exchange creation, MIC uniqueness, and timezone validation."""
    ex = ExchangeMaster.objects.create(
        code="TEST_EX",
        name="Test Exchange",
        mic="TEST",
        country="US",
        city="Test City",
        timezone="America/New_York",
    )
    assert ex.code == "TEST_EX"
    assert ex.tz_info.key == "America/New_York"

    # Duplicate MIC should raise IntegrityError
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            ExchangeMaster.objects.create(
                code="TEST_EX2",
                name="Test Exchange 2",
                mic="TEST",
                country="US",
                city="Test City",
                timezone="America/New_York",
            )

    # Invalid IANA timezone should raise ValidationError
    with pytest.raises(ValidationError):
        bad_ex = ExchangeMaster(
            code="BAD_TZ",
            name="Bad Timezone",
            mic="BADT",
            country="US",
            city="Nowhere",
            timezone="Invalid/Timezone_Name",
        )
        bad_ex.full_clean()


@pytest.mark.django_db
def test_seed_exchanges_command_and_custom_venues():
    """Verify seed_exchanges creates primary venues including IFAD, BMD, and B3."""
    call_command("seed_exchanges", "--skip-api-holidays")

    # Check venue count
    assert ExchangeMaster.objects.count() >= 15

    # Check user-requested custom exchanges
    ifad = ExchangeMaster.objects.get(code="IFAD")
    assert ifad.name == "ICE Futures Abu Dhabi"
    assert ifad.country == "AE"
    assert ifad.timezone == "Asia/Dubai"
    assert ifad.currency == "USD"

    bmd = ExchangeMaster.objects.get(code="BMD")
    assert bmd.name == "Bursa Malaysia Derivatives"
    assert bmd.mic == "XKLS"
    assert bmd.country == "MY"
    assert bmd.currency == "MYR"

    b3 = ExchangeMaster.objects.get(code="B3")
    assert b3.name == "B3 - Brasil, Bolsa, Balcão"
    assert b3.mic == "BVMF"
    assert b3.country == "BR"
    assert b3.currency == "BRL"

    # Check core benchmark venues
    assert ExchangeMaster.objects.filter(code="NYMEX").exists()
    assert ExchangeMaster.objects.filter(code="CME").exists()
    assert ExchangeMaster.objects.filter(code="ICE_EU").exists()
    assert ExchangeMaster.objects.filter(code="LME").exists()
    assert ExchangeMaster.objects.filter(code="MCX").exists()

    # Verify trading sessions created
    assert ExchangeTradingSession.objects.filter(exchange=ifad).exists()
    assert ExchangeTradingSession.objects.filter(exchange=b3).exists()
    assert ExchangeTradingSession.objects.filter(exchange=bmd).exists()


@pytest.mark.django_db
def test_is_trading_day_logic():
    """Verify weekend detection and holiday closure filtering."""
    ex = ExchangeMaster.objects.create(
        code="CAL_EX",
        name="Calendar Test",
        mic="CALT",
        country="US",
        city="Chicago",
        timezone="America/Chicago",
    )

    # Sunday (2026-09-20) -> should be False
    sunday = dt_date(2026, 9, 20)
    assert sunday.weekday() == 6
    assert ex.is_trading_day(sunday) is False

    # Saturday (2026-09-19) -> should be False
    saturday = dt_date(2026, 9, 19)
    assert saturday.weekday() == 5
    assert ex.is_trading_day(saturday) is False

    # Normal Wednesday (2026-09-23) -> should be True
    wednesday = dt_date(2026, 9, 23)
    assert wednesday.weekday() == 2
    assert ex.is_trading_day(wednesday) is True

    # Register an official full-day holiday on this Wednesday
    ExchangeHoliday.objects.create(
        exchange=ex,
        date=wednesday,
        name="Market Holiday",
        is_full_day_closure=True,
    )
    # Now Wednesday must return False!
    assert ex.is_trading_day(wednesday) is False


@pytest.mark.django_db
def test_holiday_service_and_fallbacks():
    """Verify reliable holiday synchronization with fallback handling."""
    ex = ExchangeMaster.objects.create(
        code="BR_TEST",
        name="Brazil Test Venue",
        mic="BRTT",
        country="BR",
        city="Sao Paulo",
        timezone="America/Sao_Paulo",
    )
    result = ExchangeHolidaySyncService.sync_exchange_holidays(ex, year=2026)
    assert result["synced_count"] > 0
    assert ex.holidays.count() > 0

    # Christmas closure check in Brazil
    natal = dt_date(2026, 12, 25)
    assert ex.holidays.filter(date=natal).exists()
    assert ex.is_trading_day(natal) is False


@pytest.mark.django_db
def test_exchange_api_endpoints():
    """Verify REST API endpoints for Exchange Master, detail, trading day, and summary."""
    call_command("seed_exchanges", "--skip-api-holidays")
    client = APIClient()

    # 1. Exchange List
    url_list = reverse("exchanges:exchange_list")
    resp_list = client.get(url_list)
    assert resp_list.status_code == 200
    assert len(resp_list.data) >= 15

    # Filter by country
    resp_br = client.get(f"{url_list}?country=BR")
    assert resp_br.status_code == 200
    assert len(resp_br.data) == 1
    assert resp_br.data[0]["code"] == "B3"

    # 2. Exchange Detail (lookup by code or MIC)
    url_detail_code = reverse("exchanges:exchange_detail", kwargs={"identifier": "IFAD"})
    resp_detail_code = client.get(url_detail_code)
    assert resp_detail_code.status_code == 200
    assert resp_detail_code.data["mic"] == "IFAD"
    assert "sessions" in resp_detail_code.data

    url_detail_mic = reverse("exchanges:exchange_detail", kwargs={"identifier": "XKLS"})
    resp_detail_mic = client.get(url_detail_mic)
    assert resp_detail_mic.status_code == 200
    assert resp_detail_mic.data["code"] == "BMD"

    # 3. Trading Day Evaluator Endpoint
    url_trading_day = reverse("exchanges:is_trading_day", kwargs={"identifier": "NYMEX"})
    # Query on Sunday (2026-09-20)
    resp_td_sunday = client.get(f"{url_trading_day}?date=2026-09-20")
    assert resp_td_sunday.status_code == 200
    assert resp_td_sunday.data["is_trading_day"] is False
    assert resp_td_sunday.data["is_weekend"] is True

    # 4. Summary Endpoint
    url_summary = reverse("exchanges:exchange_summary")
    resp_summary = client.get(url_summary)
    assert resp_summary.status_code == 200
    assert resp_summary.data["exchanges"]["total"] >= 15
    assert resp_summary.data["trading_sessions"] >= 10


@pytest.mark.django_db
def test_trading_vs_settlement_on_holidays():
    """
    Verify institutional trading vs settlement logic:
    - Electronic trading without settlement on CME/NYMEX (rolled trade dates)
    - Full closure on CBOT agriculture vs active NYMEX energy
    - Early close WITH settlement on Black Friday
    - Columbus Day & Veterans Day remain active trading days for US exchanges
    - MCX evening session active with settlement on festival holidays
    """
    call_command("seed_exchanges", "--skip-api-holidays")

    nymex = ExchangeMaster.objects.get(code="NYMEX")
    cbot = ExchangeMaster.objects.get(code="CBOT")
    cme = ExchangeMaster.objects.get(code="CME")
    mcx = ExchangeMaster.objects.get(code="MCX")

    # 1. Memorial Day (Last Monday of May 2026: 2026-05-25)
    memorial_day = dt_date(2026, 5, 25)

    # NYMEX: Electronic trading active without official settlement (rolls to Tuesday)
    assert nymex.is_trading_day(memorial_day) is True
    assert nymex.is_settlement_day(memorial_day) is False
    status_nymex = nymex.get_market_status(memorial_day)
    assert status_nymex["status"] == "TRADING_WITHOUT_SETTLEMENT"
    assert status_nymex["settlement_rolled"] is True
    assert "ENERGY" in status_nymex["affected_product_groups"]

    # CBOT: Agriculture pits and Globex order books completely closed
    assert cbot.is_trading_day(memorial_day, product_group="AGRICULTURE") is False
    assert cbot.is_settlement_day(memorial_day, product_group="AGRICULTURE") is False

    # 2. Black Friday 2026 (Day after Thanksgiving: 2026-11-27)
    # Trading WITH official early settlement
    black_friday = dt_date(2026, 11, 27)
    assert nymex.is_trading_day(black_friday) is True
    assert nymex.is_settlement_day(black_friday) is True
    status_bf = nymex.get_market_status(black_friday)
    assert status_bf["status"] == "EARLY_CLOSE_WITH_SETTLEMENT"
    assert status_bf["early_close_time"] == "12:30:00"

    # 3. Good Friday 2026 (2026-04-03)
    # Mandatory full dark closure on all US venues
    good_friday = dt_date(2026, 4, 3)
    assert nymex.is_trading_day(good_friday) is False
    assert nymex.is_settlement_day(good_friday) is False
    status_gf = nymex.get_market_status(good_friday)
    assert status_gf["status"] == "FULL_DAY_CLOSURE"

    # 4. Columbus Day 2026 (2026-10-12) & Veterans Day (2026-11-11)
    # Public holidays where futures exchanges remain OPEN for both trading and settlement
    columbus_day = dt_date(2026, 10, 12)
    veterans_day = dt_date(2026, 11, 11)
    assert cme.is_trading_day(columbus_day) is True
    assert cme.is_settlement_day(columbus_day) is True
    assert cme.is_trading_day(veterans_day) is True
    assert cme.is_settlement_day(veterans_day) is True

    # 5. MCX Split Session on Holi (2026-03-17)
    # Morning session closed, Evening session OPEN with settlement
    holi = dt_date(2026, 3, 17)
    assert mcx.is_trading_day(holi) is True
    assert mcx.is_settlement_day(holi) is True
    status_mcx = mcx.get_market_status(holi)
    assert status_mcx["status"] == "TRADING_WITH_SETTLEMENT"
    assert status_mcx["affected_product_groups"] == "EVENING_SESSION_OPEN"

    # MCX Full National Closure on Republic Day (2026-01-26)
    republic_day = dt_date(2026, 1, 26)
    assert mcx.is_trading_day(republic_day) is False
    assert mcx.is_settlement_day(republic_day) is False

