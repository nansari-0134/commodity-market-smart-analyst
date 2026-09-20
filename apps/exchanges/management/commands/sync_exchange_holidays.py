"""
Management command to fetch and synchronize exchange holidays from reliable public API.
"""
from django.core.management.base import BaseCommand
from apps.exchanges.models import ExchangeMaster
from apps.exchanges.services.holiday_service import ExchangeHolidaySyncService


class Command(BaseCommand):
    help = "Fetches and synchronizes exchange holidays from reliable external APIs (e.g. Nager.Date)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--exchange",
            type=str,
            help="Filter by exchange code (e.g. CME, NYMEX, B3, BMD, IFAD). Default: all active exchanges.",
        )
        parser.add_argument(
            "--year",
            type=int,
            help="Calendar year to sync (e.g. 2026). Default: current year and next year.",
        )

    def handle(self, *args, **options):
        ex_code = options.get("exchange")
        year = options.get("year")

        qs = ExchangeMaster.objects.filter(is_active=True)
        if ex_code:
            qs = qs.filter(code__iexact=ex_code)
            if not qs.exists():
                self.stderr.write(f"Exchange '{ex_code}' not found.")
                return

        self.stdout.write(self.style.NOTICE(f"Synchronizing exchange holidays for {qs.count()} venues..."))
        total_synced = 0
        for ex in qs:
            res = ExchangeHolidaySyncService.sync_exchange_holidays(ex, year=year)
            total_synced += res["synced_count"]
            self.stdout.write(f"  -> {ex.code} ({ex.country}): {res['synced_count']} holidays synchronized [{res['status']}]")

        self.stdout.write(self.style.SUCCESS(f"Total {total_synced} exchange holidays synchronized successfully."))
