"""
Django management command to seed the Provider Master catalog.

Loads benchmark external data vendors, PRAs, and exchange feeds via the pluggable
provider catalog architecture with strict idempotency and two-pass fallback resolution.
"""

from typing import Any
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.providers.models import ProviderMaster
from apps.providers.providers.factory import get_provider_catalog


class Command(BaseCommand):
    help = "Seed canonical Provider Master catalog with benchmark global data vendors and agencies."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing providers before seeding (caution: cascades to references).",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        if options["clear"]:
            count, _ = ProviderMaster.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {count} existing provider records."))

        catalog = get_provider_catalog()
        specs = catalog.get_providers()
        created_count = 0
        updated_count = 0
        fallback_links = 0

        self.stdout.write(f"Seeding {len(specs)} providers via {type(catalog).__name__}...")

        # Pass 1: Upsert core provider records
        provider_map = {}
        for spec in specs:
            provider, created = ProviderMaster.objects.update_or_create(
                code=spec.code,
                defaults={
                    "name": spec.name,
                    "description": spec.description,
                    "provider_type": spec.provider_type,
                    "base_url": spec.base_url,
                    "documentation_url": spec.documentation_url,
                    "support_contact": spec.support_contact,
                    "auth_type": spec.auth_type,
                    "env_var_name": spec.env_var_name,
                    "auth_param_name": spec.auth_param_name,
                    "rate_limit_requests": spec.rate_limit_requests,
                    "rate_limit_window_seconds": spec.rate_limit_window_seconds,
                    "backoff_seconds": spec.backoff_seconds,
                    "target_sla_pct": spec.target_sla_pct,
                    "is_active": spec.is_active,
                    "display_order": spec.display_order,
                    "notes": spec.notes,
                },
            )
            provider_map[spec.code] = provider
            if created:
                created_count += 1
            else:
                updated_count += 1

        # Pass 2: Resolve and link fallback providers
        for spec in specs:
            if spec.fallback_code and spec.fallback_code in provider_map:
                provider = provider_map[spec.code]
                fallback_target = provider_map[spec.fallback_code]
                if provider.fallback_provider_id != fallback_target.id:
                    provider.fallback_provider = fallback_target
                    provider.save(update_fields=["fallback_provider"])
                    fallback_links += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {len(specs)} providers "
                f"({created_count} created, {updated_count} updated, {fallback_links} fallback links resolved)."
            )
        )
