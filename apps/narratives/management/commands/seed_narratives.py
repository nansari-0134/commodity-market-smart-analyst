"""
Management command to seed initial baseline Market Narratives idempotently.
"""
from django.core.management.base import BaseCommand
from apps.commodities.models import CommodityMaster
from apps.narratives.models import MarketNarrative, NarrativeType
from apps.narratives.services.generator import generate_market_narrative


class Command(BaseCommand):
    help = "Seeds baseline AI Market Narratives for benchmark commodities."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing narratives before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            count = MarketNarrative.objects.count()
            MarketNarrative.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {count} existing MarketNarrative records."))

        benchmarks = ["CL", "BRENT", "NG", "GOLD", "CORN"]
        types = [
            NarrativeType.MORNING_BRIEF,
            NarrativeType.SUPPLY_DEMAND,
            NarrativeType.RISK_ALERT,
        ]

        created_count = 0
        for code in benchmarks:
            commodity = CommodityMaster.objects.filter(code=code).first()
            if not commodity:
                continue

            for n_type in types:
                # Idempotency check: if one exists within today, skip
                exists = MarketNarrative.objects.filter(
                    commodity=commodity,
                    narrative_type=n_type,
                ).exists()

                if not exists or options["clear"]:
                    generate_market_narrative(
                        commodity_code=code,
                        narrative_type=n_type,
                        provider_name="static",
                    )
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {created_count} Market Narratives across benchmark commodities.")
        )
