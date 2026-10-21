"""
Management command to generate a Market Narrative on-demand.
"""
from django.core.management.base import BaseCommand, CommandError
from apps.narratives.models import NarrativeType
from apps.narratives.services.generator import generate_market_narrative


class Command(BaseCommand):
    help = "Generates an evidence-grounded AI Market Narrative on-demand."

    def add_arguments(self, parser):
        parser.add_argument(
            "--commodity",
            type=str,
            default="CL",
            help="Commodity symbol (e.g., CL, BRENT, NG, GOLD, CORN)",
        )
        parser.add_argument(
            "--type",
            type=str,
            default="MORNING_BRIEF",
            choices=[
                "MORNING_BRIEF",
                "EXECUTIVE_FLASH",
                "SUPPLY_DEMAND",
                "RISK_ALERT",
                "OUTLIER_DIVERGENCE",
            ],
            help="Type of narrative to generate",
        )
        parser.add_argument(
            "--provider",
            type=str,
            default=None,
            help="LLM provider override (static, gemini, claude, openai, ollama)",
        )

    def handle(self, *args, **options):
        symbol = options["commodity"].upper()
        n_type = options["type"]
        provider = options["provider"]

        self.stdout.write(f"Generating {n_type} for {symbol} (provider: {provider or 'configured default'})...")
        try:
            narrative = generate_market_narrative(
                commodity_code=symbol,
                narrative_type=n_type,
                provider_name=provider,
            )
            self.stdout.write(self.style.SUCCESS(f"Published Narrative ID: {narrative.id}"))
            self.stdout.write(self.style.SUCCESS(f"Headline: {narrative.headline}"))
            self.stdout.write(f"Summary: {narrative.executive_summary}\n")
        except Exception as exc:
            raise CommandError(f"Narrative generation failed: {exc}")
