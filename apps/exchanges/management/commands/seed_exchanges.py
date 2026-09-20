"""
Management command to seed global commodity exchanges, trading sessions, and holidays.
"""
from datetime import time
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.exchanges.models import (
    ExchangeMaster,
    ExchangeTier,
    ExchangeTradingSession,
    SessionType,
)
from apps.exchanges.services.holiday_service import ExchangeHolidaySyncService


class Command(BaseCommand):
    help = "Seeds major global commodity exchanges, operating sessions, and holiday calendars."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-api-holidays",
            action="store_true",
            help="Skip remote API holiday sync and use only deterministic seed holidays.",
        )

    def handle(self, *args, **options):
        skip_api = options.get("skip_api_holidays", False)
        self.stdout.write(self.style.NOTICE("Seeding global commodity exchanges..."))

        with transaction.atomic():
            exchanges = self._seed_exchanges()
            self._seed_sessions(exchanges)

        self.stdout.write(self.style.NOTICE("Synchronizing exchange trading holiday calendars..."))
        for code, ex in exchanges.items():
            res = ExchangeHolidaySyncService.sync_exchange_holidays(
                ex,
                use_fallback_if_failed=True,
                skip_remote_api=skip_api,
            )
            self.stdout.write(f"  -> {code} ({ex.country}): {res['synced_count']} holidays synchronized [{res['status']}].")

        self.stdout.write(self.style.SUCCESS("Exchange Master seeding and holiday synchronization complete."))

    def _seed_exchanges(self):
        venue_data = [
            # NORTH AMERICA
            {
                "code": "CME",
                "name": "Chicago Mercantile Exchange",
                "mic": "XCME",
                "operating_mic": "XCME",
                "country": "US",
                "city": "Chicago",
                "timezone": "America/Chicago",
                "currency": "USD",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.cmegroup.com",
            },
            {
                "code": "NYMEX",
                "name": "New York Mercantile Exchange",
                "mic": "XNYM",
                "operating_mic": "XCME",
                "country": "US",
                "city": "New York",
                "timezone": "America/New_York",
                "currency": "USD",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.cmegroup.com/markets/energy.html",
            },
            {
                "code": "COMEX",
                "name": "Commodity Exchange (COMEX)",
                "mic": "XCEC",
                "operating_mic": "XCME",
                "country": "US",
                "city": "New York",
                "timezone": "America/New_York",
                "currency": "USD",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.cmegroup.com/markets/metals.html",
            },
            {
                "code": "CBOT",
                "name": "Chicago Board of Trade",
                "mic": "XCBT",
                "operating_mic": "XCME",
                "country": "US",
                "city": "Chicago",
                "timezone": "America/Chicago",
                "currency": "USD",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.cmegroup.com/markets/agriculture.html",
            },
            {
                "code": "ICE_US",
                "name": "ICE Futures U.S.",
                "mic": "IFUS",
                "operating_mic": "IFUS",
                "country": "US",
                "city": "New York",
                "timezone": "America/New_York",
                "currency": "USD",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.theice.com/futures-us",
            },
            # EUROPE
            {
                "code": "ICE_EU",
                "name": "ICE Futures Europe",
                "mic": "IFEU",
                "operating_mic": "IFEU",
                "country": "GB",
                "city": "London",
                "timezone": "Europe/London",
                "currency": "USD",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.theice.com/futures-europe",
            },
            {
                "code": "LME",
                "name": "London Metal Exchange",
                "mic": "XLME",
                "operating_mic": "XLME",
                "country": "GB",
                "city": "London",
                "timezone": "Europe/London",
                "currency": "USD",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.lme.com",
            },
            {
                "code": "EEX",
                "name": "European Energy Exchange",
                "mic": "XEEE",
                "operating_mic": "XEEE",
                "country": "DE",
                "city": "Leipzig",
                "timezone": "Europe/Berlin",
                "currency": "EUR",
                "tier": ExchangeTier.REGIONAL_PRIMARY,
                "website_url": "https://www.eex.com",
            },
            # MIDDLE EAST (User requested: ICE Futures Abu Dhabi)
            {
                "code": "IFAD",
                "name": "ICE Futures Abu Dhabi",
                "mic": "IFAD",
                "operating_mic": "IFAD",
                "country": "AE",
                "city": "Abu Dhabi",
                "timezone": "Asia/Dubai",
                "currency": "USD",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.theice.com/futures-abu-dhabi",
            },
            # SOUTH AMERICA (User requested: B3 Exchange)
            {
                "code": "B3",
                "name": "B3 - Brasil, Bolsa, Balcão",
                "mic": "BVMF",
                "operating_mic": "BVMF",
                "country": "BR",
                "city": "São Paulo",
                "timezone": "America/Sao_Paulo",
                "currency": "BRL",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.b3.com.br",
            },
            # SOUTHEAST ASIA (User requested: Bursa Malaysia)
            {
                "code": "BMD",
                "name": "Bursa Malaysia Derivatives",
                "mic": "XKLS",
                "operating_mic": "XKLS",
                "country": "MY",
                "city": "Kuala Lumpur",
                "timezone": "Asia/Kuala_Lumpur",
                "currency": "MYR",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.bursamalaysia.com",
            },
            {
                "code": "SGX",
                "name": "Singapore Exchange",
                "mic": "XSES",
                "operating_mic": "XSES",
                "country": "SG",
                "city": "Singapore",
                "timezone": "Asia/Singapore",
                "currency": "USD",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "https://www.sgx.com",
            },
            # ASIA & OTHER
            {
                "code": "SHFE",
                "name": "Shanghai Futures Exchange",
                "mic": "XSGE",
                "operating_mic": "XSGE",
                "country": "CN",
                "city": "Shanghai",
                "timezone": "Asia/Shanghai",
                "currency": "CNY",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "http://www.shfe.com.cn",
            },
            {
                "code": "DCE",
                "name": "Dalian Commodity Exchange",
                "mic": "XDCE",
                "operating_mic": "XDCE",
                "country": "CN",
                "city": "Dalian",
                "timezone": "Asia/Shanghai",
                "currency": "CNY",
                "tier": ExchangeTier.GLOBAL_BENCHMARK,
                "website_url": "http://www.dce.com.cn",
            },
            {
                "code": "MCX",
                "name": "Multi Commodity Exchange of India",
                "mic": "XMCX",
                "operating_mic": "XMCX",
                "country": "IN",
                "city": "Mumbai",
                "timezone": "Asia/Kolkata",
                "currency": "INR",
                "tier": ExchangeTier.REGIONAL_PRIMARY,
                "website_url": "https://www.mcxindia.com",
            },
        ]

        exchanges = {}
        for v in venue_data:
            obj, _ = ExchangeMaster.objects.update_or_create(
                code=v["code"],
                defaults={
                    "name": v["name"],
                    "mic": v["mic"],
                    "operating_mic": v["operating_mic"],
                    "country": v["country"],
                    "city": v["city"],
                    "timezone": v["timezone"],
                    "currency": v["currency"],
                    "tier": v["tier"],
                    "website_url": v["website_url"],
                    "is_active": True,
                },
            )
            exchanges[v["code"]] = obj

        self.stdout.write(f"  -> Total Exchanges Seeded: {len(exchanges)}")
        return exchanges

    def _seed_sessions(self, exchanges):
        self.stdout.write("Seeding operating trading sessions and settlement windows...")

        session_configs = [
            # CME Globex Core
            {"exchange": "CME", "name": "CME Globex Electronic Session", "type": SessionType.ELECTRONIC, "start": time(17, 0), "end": time(16, 0), "days": "SUN,MON,TUE,WED,THU,FRI"},
            {"exchange": "CME", "name": "CME Daily Maintenance Pause", "type": SessionType.MAINTENANCE_PAUSE, "start": time(16, 0), "end": time(17, 0), "days": "MON,TUE,WED,THU"},

            # NYMEX Energy
            {"exchange": "NYMEX", "name": "Globex Energy Trading", "type": SessionType.ELECTRONIC, "start": time(18, 0), "end": time(17, 0), "days": "SUN,MON,TUE,WED,THU,FRI"},
            {"exchange": "NYMEX", "name": "WTI Official Daily Settlement Window", "type": SessionType.SETTLEMENT_WINDOW, "start": time(14, 28), "end": time(14, 30), "days": "MON,TUE,WED,THU,FRI"},

            # CBOT Grains
            {"exchange": "CBOT", "name": "CBOT Grains Overnight & Day Session", "type": SessionType.ELECTRONIC, "start": time(19, 0), "end": time(13, 20), "days": "SUN,MON,TUE,WED,THU,FRI"},
            {"exchange": "CBOT", "name": "Grains Official Settlement Window", "type": SessionType.SETTLEMENT_WINDOW, "start": time(13, 14), "end": time(13, 15), "days": "MON,TUE,WED,THU,FRI"},

            # ICE Futures Europe
            {"exchange": "ICE_EU", "name": "ICE Europe Continuous Electronic", "type": SessionType.ELECTRONIC, "start": time(1, 0), "end": time(23, 0), "days": "MON,TUE,WED,THU,FRI"},
            {"exchange": "ICE_EU", "name": "Brent Crude Settlement Window", "type": SessionType.SETTLEMENT_WINDOW, "start": time(19, 28), "end": time(19, 30), "days": "MON,TUE,WED,THU,FRI"},

            # IFAD (ICE Futures Abu Dhabi)
            {"exchange": "IFAD", "name": "IFAD Murban Trading Session", "type": SessionType.ELECTRONIC, "start": time(1, 0), "end": time(0, 0), "days": "MON,TUE,WED,THU,FRI"},
            {"exchange": "IFAD", "name": "Murban Crude Settlement Window", "type": SessionType.SETTLEMENT_WINDOW, "start": time(19, 28), "end": time(19, 30), "days": "MON,TUE,WED,THU,FRI"},

            # B3 Brasil
            {"exchange": "B3", "name": "B3 Commodities Regular Trading", "type": SessionType.ELECTRONIC, "start": time(9, 0), "end": time(18, 0), "days": "MON,TUE,WED,THU,FRI"},
            {"exchange": "B3", "name": "B3 Agricultural Settlement Window", "type": SessionType.SETTLEMENT_WINDOW, "start": time(16, 0), "end": time(16, 15), "days": "MON,TUE,WED,THU,FRI"},

            # BMD (Bursa Malaysia Derivatives)
            {"exchange": "BMD", "name": "BMD Morning Session", "type": SessionType.ELECTRONIC, "start": time(10, 30), "end": time(12, 30), "days": "MON,TUE,WED,THU,FRI"},
            {"exchange": "BMD", "name": "BMD Afternoon Session", "type": SessionType.ELECTRONIC, "start": time(14, 30), "end": time(18, 0), "days": "MON,TUE,WED,THU,FRI"},
            {"exchange": "BMD", "name": "FCPO Palm Oil Settlement Window", "type": SessionType.SETTLEMENT_WINDOW, "start": time(17, 50), "end": time(18, 0), "days": "MON,TUE,WED,THU,FRI"},

            # LME London Metal Exchange
            {"exchange": "LME", "name": "LME Select Electronic", "type": SessionType.ELECTRONIC, "start": time(1, 0), "end": time(19, 0), "days": "MON,TUE,WED,THU,FRI"},
            {"exchange": "LME", "name": "LME Ring / Kerb Official Prices", "type": SessionType.OPEN_OUTCRY, "start": time(12, 30), "end": time(13, 15), "days": "MON,TUE,WED,THU,FRI"},

            # MCX India
            {"exchange": "MCX", "name": "MCX Non-Agri / Energy Trading", "type": SessionType.ELECTRONIC, "start": time(9, 0), "end": time(23, 30), "days": "MON,TUE,WED,THU,FRI"},
        ]

        for s in session_configs:
            ex_obj = exchanges.get(s["exchange"])
            if not ex_obj:
                continue
            ExchangeTradingSession.objects.update_or_create(
                exchange=ex_obj,
                name=s["name"],
                defaults={
                    "session_type": s["type"],
                    "start_time_local": s["start"],
                    "end_time_local": s["end"],
                    "days_of_week": s["days"],
                    "is_active": True,
                },
            )
        self.stdout.write(f"  -> Total Operating Sessions Seeded: {ExchangeTradingSession.objects.count()}")
