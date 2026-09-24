"""
Management command to seed canonical API endpoint specifications.
Follows the Pluggable Provider Architecture via get_endpoint_catalog().
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.datasets.models import DatasetMaster
from apps.endpoints.models import EndpointMaster
from apps.endpoints.providers.factory import get_endpoint_catalog
from apps.providers.models import ProviderMaster


class Command(BaseCommand):
    help = "Seeds canonical endpoint and API metadata specifications across global commodity providers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing endpoints before seeding.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding canonical endpoint master catalog..."))

        provider = get_endpoint_catalog()
        specs = provider.get_endpoints()

        with transaction.atomic():
            if options.get("clear"):
                self.stdout.write(self.style.WARNING("Clearing existing endpoint records..."))
                EndpointMaster.objects.all().delete()

            # Pre-cache lookups
            providers = {p.code.upper(): p for p in ProviderMaster.objects.all()}
            datasets = {d.code.upper(): d for d in DatasetMaster.objects.all()}

            created_count = 0
            updated_count = 0

            for raw in specs:
                parent_provider = providers.get(raw.provider_code.upper())
                if not parent_provider:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Provider '{raw.provider_code}' not found for endpoint {raw.code}. Skipping."
                        )
                    )
                    continue

                target_dataset = datasets.get(raw.dataset_code.upper()) if raw.dataset_code else None

                defaults = {
                    "name": raw.name,
                    "description": raw.description,
                    "provider": parent_provider,
                    "dataset": target_dataset,
                    "protocol": raw.protocol,
                    "http_method": raw.http_method,
                    "path_template": raw.path_template,
                    "response_format": raw.response_format,
                    "data_envelope_path": raw.data_envelope_path,
                    "default_params": raw.default_params,
                    "custom_headers": raw.custom_headers,
                    "cache_ttl_seconds": raw.cache_ttl_seconds,
                    "is_active": raw.is_active,
                    "notes": raw.notes,
                }

                _, created = EndpointMaster.objects.update_or_create(
                    code=raw.code,
                    defaults=defaults,
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully processed {len(specs)} endpoints: "
                    f"{created_count} created, {updated_count} updated."
                )
            )
