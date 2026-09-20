"""
Service to fetch, synchronize, and calibrate exchange holiday and trading calendars.
Implements institutional rules distinguishing between public civic holidays, trading
sessions without settlement (rolled trade dates), early closes with settlement,
and product-group-specific closures.
"""
from datetime import datetime, date as dt_date, time, timedelta
import logging
from typing import Dict, Any, List, Tuple
import httpx
from django.utils import timezone
from apps.exchanges.models import ExchangeMaster, ExchangeHoliday

logger = logging.getLogger("apps.exchanges")

# Reliable public holiday API (Nager.Date v3)
NAGER_DATE_API_URL = "https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"

# Civilian/Bank holidays where US commodity exchanges REMAIN OPEN for trading
CIVIC_HOLIDAYS_US_EXCHANGES_OPEN = ["columbus", "indigenous", "veterans"]

# High-confidence statutory public holidays for offline and fallback operation
DEFAULT_CORE_HOLIDAYS: Dict[str, List[Tuple[str, str]]] = {
    "US": [
        ("New Year's Day", "01-01"),
        ("Martin Luther King Jr. Day", "01-19"),
        ("Presidents' Day", "02-16"),
        ("Memorial Day", "05-25"),
        ("Juneteenth National Independence Day", "06-19"),
        ("Independence Day", "07-04"),
        ("Labor Day", "09-07"),
        ("Thanksgiving Day", "11-26"),
        ("Christmas Day", "12-25"),
    ],
    "GB": [
        ("New Year's Day", "01-01"),
        ("Good Friday", "04-03"),
        ("Easter Monday", "04-06"),
        ("Early May Bank Holiday", "05-04"),
        ("Spring Bank Holiday", "05-25"),
        ("Summer Bank Holiday", "08-31"),
        ("Christmas Day", "12-25"),
        ("Boxing Day", "12-26"),
    ],
    "BR": [
        ("Confraternização Universal", "01-01"),
        ("Carnaval", "02-17"),
        ("Sexta-feira Santa", "04-03"),
        ("Tiradentes", "04-21"),
        ("Dia do Trabalho", "05-01"),
        ("Corpus Christi", "06-04"),
        ("Independência do Brasil", "09-07"),
        ("Nossa Senhora Aparecida", "10-12"),
        ("Finados", "11-02"),
        ("Proclamação da República", "11-15"),
        ("Natal", "12-25"),
    ],
    "MY": [
        ("New Year's Day", "01-01"),
        ("Chinese New Year", "01-29"),
        ("Hari Raya Aidilfitri", "03-31"),
        ("Labour Day", "05-01"),
        ("Wesak Day", "05-12"),
        ("Agong's Birthday", "06-01"),
        ("National Day", "08-31"),
        ("Malaysia Day", "09-16"),
        ("Deepavali", "10-20"),
        ("Christmas Day", "12-25"),
    ],
    "AE": [
        ("New Year's Day", "01-01"),
        ("Eid Al-Fitr", "03-30"),
        ("Arafat Day", "06-05"),
        ("Eid Al-Adha", "06-06"),
        ("Islamic New Year", "06-26"),
        ("National Day", "12-02"),
    ],
    "IN": [
        ("Republic Day", "01-26"),
        ("Mahashivratri", "02-26"),
        ("Holi", "03-17"),
        ("Ambedkar Jayanti", "04-14"),
        ("Eid-ul-Fitr", "03-31"),
        ("Maharashtra Day", "05-01"),
        ("Bakri Id", "06-07"),
        ("Muharram", "07-06"),
        ("Independence Day", "08-15"),
        ("Mahatma Gandhi Jayanti", "10-02"),
        ("Dussehra", "10-21"),
        ("Diwali (Laxmi Pujan)", "11-09"),
        ("Gurunanak Jayanti", "11-24"),
        ("Christmas Day", "12-25"),
    ],
    "SG": [
        ("New Year's Day", "01-01"),
        ("Chinese New Year", "01-29"),
        ("Hari Raya Puasa", "03-31"),
        ("Labour Day", "05-01"),
        ("Vesak Day", "05-12"),
        ("Hari Raya Haji", "06-07"),
        ("National Day", "08-09"),
        ("Deepavali", "10-20"),
        ("Christmas Day", "12-25"),
    ],
    "CN": [
        ("New Year's Day", "01-01"),
        ("Spring Festival", "01-29"),
        ("Tomb Sweeping Day", "04-04"),
        ("Labour Day", "05-01"),
        ("Dragon Boat Festival", "05-31"),
        ("Mid-Autumn Festival", "10-06"),
        ("National Day", "10-01"),
    ],
    "DE": [
        ("Neujahr", "01-01"),
        ("Karfreitag", "04-03"),
        ("Ostermontag", "04-06"),
        ("Tag der Arbeit", "05-01"),
        ("Christi Himmelfahrt", "05-14"),
        ("Pfingstmontag", "05-25"),
        ("Tag der Deutschen Einheit", "10-03"),
        ("1. Weihnachtstag", "12-25"),
        ("2. Weihnachtstag", "12-26"),
    ],
}


def calculate_easter_sunday(year: int) -> dt_date:
    """Meeus/Jones/Butcher algorithm for Gregorian Easter Sunday."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return dt_date(year, month, day)


def calculate_good_friday(year: int) -> dt_date:
    """Returns Good Friday for the specified calendar year."""
    return calculate_easter_sunday(year) - timedelta(days=2)


def calculate_thanksgiving(year: int) -> dt_date:
    """Thanksgiving in the US is always the 4th Thursday of November."""
    nov_1 = dt_date(year, 11, 1)
    days_to_first_thursday = (3 - nov_1.weekday()) % 7
    first_thursday = nov_1 + timedelta(days=days_to_first_thursday)
    return first_thursday + timedelta(weeks=3)


def calculate_black_friday(year: int) -> dt_date:
    """Day after Thanksgiving."""
    return calculate_thanksgiving(year) + timedelta(days=1)


class ExchangeHolidaySyncService:
    """
    Synchronizes exchange holidays from external APIs and calibrates them with institutional
    exchange trading rules, settlement windows, and product-specific closures.
    """

    @classmethod
    def sync_exchange_holidays(
        cls,
        exchange: ExchangeMaster,
        year: int | None = None,
        use_fallback_if_failed: bool = True,
        skip_remote_api: bool = False,
    ) -> Dict[str, Any]:
        """
        Fetches and calibrates holidays for the exchange venue for the specified year(s).
        """
        current_year = year or timezone.now().year
        years_to_sync = [current_year, current_year + 1] if year is None else [year]

        total_synced = 0
        errors: List[str] = []

        for y in years_to_sync:
            if skip_remote_api:
                fallback_count = cls._seed_fallback_holidays(exchange, y)
                total_synced += fallback_count
            else:
                synced_count, error = cls._fetch_and_store_holidays(exchange, y)
                if error:
                    errors.append(error)
                    if use_fallback_if_failed:
                        fallback_count = cls._seed_fallback_holidays(exchange, y)
                        total_synced += fallback_count
                else:
                    total_synced += synced_count

            # Enforce institutional venue calendar rules (early closes, Good Friday, Black Friday)
            injected_count = cls._apply_institutional_calendar_rules(exchange, y)
            total_synced += injected_count

        return {
            "exchange": exchange.code,
            "country": exchange.country,
            "synced_count": total_synced,
            "errors": errors,
            "status": "success" if not errors else ("partial_fallback" if use_fallback_if_failed else "error"),
        }

    @classmethod
    def _fetch_and_store_holidays(cls, exchange: ExchangeMaster, year: int) -> tuple[int, str | None]:
        url = NAGER_DATE_API_URL.format(year=year, country_code=exchange.country.upper())
        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.get(url)
                if response.status_code != 200:
                    return 0, f"API returned HTTP {response.status_code} for {exchange.country} ({year})"
                data = response.json()
        except Exception as exc:
            logger.warning(f"Could not connect to holiday API for {exchange.code}: {exc}")
            return 0, f"Network/Connection error for {exchange.country}: {str(exc)}"

        count = 0
        for item in data:
            date_str = item.get("date")
            name = item.get("localName") or item.get("name") or "Public Holiday"
            if not date_str:
                continue
            try:
                holiday_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            # Check if this public holiday should be filtered out or calibrated for this exchange
            calibrated = cls._calibrate_holiday_record(exchange, holiday_date, name, "NAGER_DATE_API")
            if calibrated is None:
                # Deliberately ignored (e.g. Columbus Day / Veterans Day on CME)
                continue

            ExchangeHoliday.objects.update_or_create(
                exchange=exchange,
                date=holiday_date,
                defaults=calibrated,
            )
            count += 1

        return count, None

    @classmethod
    def _seed_fallback_holidays(cls, exchange: ExchangeMaster, year: int) -> int:
        """Applies statutory fallback holidays calibrated for exchange trading."""
        holidays_list = DEFAULT_CORE_HOLIDAYS.get(exchange.country.upper(), [])
        count = 0
        for name, mm_dd in holidays_list:
            try:
                holiday_date = datetime.strptime(f"{year}-{mm_dd}", "%Y-%m-%d").date()
            except ValueError:
                continue

            calibrated = cls._calibrate_holiday_record(exchange, holiday_date, name, "DETERMINISTIC_FALLBACK")
            if calibrated is None:
                continue

            ExchangeHoliday.objects.update_or_create(
                exchange=exchange,
                date=holiday_date,
                defaults=calibrated,
            )
            count += 1
        return count

    @classmethod
    def _calibrate_holiday_record(
        cls,
        exchange: ExchangeMaster,
        holiday_date: dt_date,
        name: str,
        source: str,
    ) -> Dict[str, Any] | None:
        """
        Calibrates raw public holiday into institutional exchange operating rules:
        - Filters out civic holidays where futures exchanges remain open (Columbus Day, Veterans Day)
        - Models trading without settlement (CME/NYMEX holiday electronic sessions)
        - Models split sessions (MCX evening open)
        """
        name_lower = name.lower()

        # 1. US EXCHANGES (CME, NYMEX, COMEX, CBOT, ICE_US)
        if exchange.country == "US":
            # Rule A: Columbus Day / Veterans Day -> Exchanges are OPEN for trading & settlement!
            for civic_name in CIVIC_HOLIDAYS_US_EXCHANGES_OPEN:
                if civic_name in name_lower:
                    # Do not register a holiday closure!
                    return None

            # Rule B: Full Dark closures (Christmas Day, New Year's Day)
            if "christmas" in name_lower or "new year" in name_lower:
                return {
                    "name": name,
                    "is_full_day_closure": True,
                    "has_trading": False,
                    "has_settlement": False,
                    "settlement_rolled_to_next_day": False,
                    "affected_product_groups": "ALL",
                    "early_close_time_local": None,
                    "source_api": source,
                    "is_active": True,
                }

            # Rule C: Good Friday (Always full closure)
            if "good friday" in name_lower:
                return {
                    "name": name,
                    "is_full_day_closure": True,
                    "has_trading": False,
                    "has_settlement": False,
                    "settlement_rolled_to_next_day": False,
                    "affected_product_groups": "ALL",
                    "early_close_time_local": None,
                    "source_api": source,
                    "is_active": True,
                }

            # Rule D: US Federal Holidays with Electronic Trading WITHOUT Settlement
            # (MLK, Presidents', Memorial, Juneteenth, July 4th, Labor Day, Thanksgiving)
            is_cme_holiday_session = any(h in name_lower for h in [
                "martin luther", "presidents", "washington", "memorial",
                "juneteenth", "independence", "labor", "thanksgiving"
            ])

            if is_cme_holiday_session:
                if exchange.code in ("CME", "NYMEX", "COMEX"):
                    # Energy and Metals trade until 12:30 CT (13:30 ET) without settlement
                    return {
                        "name": f"{name} (Electronic Trading / Rolled Settlement)",
                        "is_full_day_closure": False,
                        "has_trading": True,
                        "has_settlement": False,
                        "settlement_rolled_to_next_day": True,
                        "early_close_time_local": time(12, 30),
                        "affected_product_groups": "ENERGY,METALS",
                        "source_api": source,
                        "is_active": True,
                    }
                elif exchange.code == "CBOT":
                    # Agriculture pit & electronic order books completely halted on holidays
                    return {
                        "name": f"{name} (Ag Pits & Globex Closed)",
                        "is_full_day_closure": True,
                        "has_trading": False,
                        "has_settlement": False,
                        "settlement_rolled_to_next_day": False,
                        "affected_product_groups": "AGRICULTURE",
                        "early_close_time_local": None,
                        "source_api": source,
                        "is_active": True,
                    }
                elif exchange.code == "ICE_US":
                    return {
                        "name": f"{name} (Early Electronic Close)",
                        "is_full_day_closure": False,
                        "has_trading": True,
                        "has_settlement": False,
                        "settlement_rolled_to_next_day": True,
                        "early_close_time_local": time(13, 0),
                        "affected_product_groups": "SOFTS",
                        "source_api": source,
                        "is_active": True,
                    }

        # 2. INDIA - MCX SPLIT SESSIONS
        if exchange.code == "MCX":
            # National Days: Completely dark (both morning and evening sessions closed)
            if any(nat in name_lower for nat in ["republic", "independence", "gandhi"]):
                return {
                    "name": f"{name} (Full Day Closure)",
                    "is_full_day_closure": True,
                    "has_trading": False,
                    "has_settlement": False,
                    "settlement_rolled_to_next_day": False,
                    "affected_product_groups": "ALL",
                    "early_close_time_local": None,
                    "source_api": source,
                    "is_active": True,
                }
            else:
                # Religious & festival holidays: Morning closed (09:00-17:00), Evening OPEN (17:00-23:30/23:55) with settlement!
                return {
                    "name": f"{name} (Morning Closed / Evening Session OPEN)",
                    "is_full_day_closure": False,
                    "has_trading": True,
                    "has_settlement": True,
                    "settlement_rolled_to_next_day": False,
                    "affected_product_groups": "EVENING_SESSION_OPEN",
                    "early_close_time_local": None,
                    "source_api": source,
                    "is_active": True,
                }

        # 3. DEFAULT GLOBAL CALENDAR
        return {
            "name": name,
            "is_full_day_closure": True,
            "has_trading": False,
            "has_settlement": False,
            "settlement_rolled_to_next_day": False,
            "affected_product_groups": "ALL",
            "early_close_time_local": None,
            "source_api": source,
            "is_active": True,
        }

    @classmethod
    def _apply_institutional_calendar_rules(cls, exchange: ExchangeMaster, year: int) -> int:
        """
        Injects mandatory market closures (Good Friday) and scheduled early-close days
        with official settlement (Black Friday, Christmas Eve, NYE, July 3rd).
        """
        injected = 0

        # Rule 1: Good Friday is a mandatory global trading closure for US, UK, DE, and SG
        if exchange.country in ("US", "GB", "DE", "SG"):
            good_friday_date = calculate_good_friday(year)
            _, created = ExchangeHoliday.objects.update_or_create(
                exchange=exchange,
                date=good_friday_date,
                defaults={
                    "name": "Good Friday",
                    "is_full_day_closure": True,
                    "has_trading": False,
                    "has_settlement": False,
                    "settlement_rolled_to_next_day": False,
                    "affected_product_groups": "ALL",
                    "early_close_time_local": None,
                    "source_api": "EXCHANGE_CALENDAR_RULE",
                    "is_active": True,
                },
            )
            if created:
                injected += 1

        # Rule 2: Scheduled Early Closes WITH Settlement for US Venues
        if exchange.country == "US":
            # Day after Thanksgiving (Black Friday)
            black_friday_date = calculate_black_friday(year)
            ExchangeHoliday.objects.update_or_create(
                exchange=exchange,
                date=black_friday_date,
                defaults={
                    "name": "Day After Thanksgiving (Black Friday Early Close)",
                    "is_full_day_closure": False,
                    "has_trading": True,
                    "has_settlement": True,
                    "settlement_rolled_to_next_day": False,
                    "affected_product_groups": "ALL",
                    "early_close_time_local": time(12, 30),
                    "source_api": "EXCHANGE_CALENDAR_RULE",
                    "is_active": True,
                },
            )
            injected += 1

            # Christmas Eve (Dec 24) - If on a weekday
            xmas_eve = dt_date(year, 12, 24)
            if xmas_eve.weekday() < 5:
                ExchangeHoliday.objects.update_or_create(
                    exchange=exchange,
                    date=xmas_eve,
                    defaults={
                        "name": "Christmas Eve (Early Close)",
                        "is_full_day_closure": False,
                        "has_trading": True,
                        "has_settlement": True,
                        "settlement_rolled_to_next_day": False,
                        "affected_product_groups": "ALL",
                        "early_close_time_local": time(12, 30),
                        "source_api": "EXCHANGE_CALENDAR_RULE",
                        "is_active": True,
                    },
                )
                injected += 1

            # New Year's Eve (Dec 31) - If on a weekday
            nye = dt_date(year, 12, 31)
            if nye.weekday() < 5:
                ExchangeHoliday.objects.update_or_create(
                    exchange=exchange,
                    date=nye,
                    defaults={
                        "name": "New Year's Eve (Early Close)",
                        "is_full_day_closure": False,
                        "has_trading": True,
                        "has_settlement": True,
                        "settlement_rolled_to_next_day": False,
                        "affected_product_groups": "ALL",
                        "early_close_time_local": time(13, 0),
                        "source_api": "EXCHANGE_CALENDAR_RULE",
                        "is_active": True,
                    },
                )
                injected += 1

            # Eve of Independence Day (July 3) - If on a weekday
            july_3 = dt_date(year, 7, 3)
            if july_3.weekday() < 5:
                ExchangeHoliday.objects.update_or_create(
                    exchange=exchange,
                    date=july_3,
                    defaults={
                        "name": "Day Before Independence Day (Early Close)",
                        "is_full_day_closure": False,
                        "has_trading": True,
                        "has_settlement": True,
                        "settlement_rolled_to_next_day": False,
                        "affected_product_groups": "ALL",
                        "early_close_time_local": time(12, 0),
                        "source_api": "EXCHANGE_CALENDAR_RULE",
                        "is_active": True,
                    },
                )
                injected += 1

        return injected
