"""
Management command to seed canonical dataset catalog entries.
Follows the Pluggable Provider Architecture via get_dataset_provider().
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.commodities.models import CommodityMaster
from apps.datasets.models import (
    DatasetMaster,
    DataCategory,
    UpdateCadence,
    IngestionMode,
    RetentionPolicy,
    LicenseType,
)
from apps.datasets.providers.factory import get_dataset_provider
from apps.exchanges.models import ExchangeMaster
from apps.metadata.models import DataDomainMaster, FrequencyMaster


class Command(BaseCommand):
    help = "Seeds canonical dataset master specifications across global commodity domains."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing datasets before seeding.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding canonical dataset master catalog..."))

        provider = get_dataset_provider()
        specs = provider.get_datasets()

        with transaction.atomic():
            if options.get("clear"):
                self.stdout.write(self.style.WARNING("Clearing existing dataset master records..."))
                DatasetMaster.objects.all().delete()

            # Pre-cache lookups
            domains = {d.code.upper(): d for d in DataDomainMaster.objects.all()}
            frequencies = {f.code.upper(): f for f in FrequencyMaster.objects.all()}
            commodities = {c.code.upper(): c for c in CommodityMaster.objects.all()}
            exchanges = {e.code.upper(): e for e in ExchangeMaster.objects.all()}

            datasets_seeded = 0

            for raw in specs:
                domain = domains.get(raw.domain_code.upper())
                if not domain:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Domain '{raw.domain_code}' not found for dataset {raw.code}. Skipping."
                        )
                    )
                    continue

                frequency = frequencies.get(raw.frequency_code.upper())
                if not frequency:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Frequency '{raw.frequency_code}' not found for dataset {raw.code}. Skipping."
                        )
                    )
                    continue

                exchange = exchanges.get(raw.exchange_code.upper()) if raw.exchange_code else None
                primary_commodity = commodities.get(raw.primary_commodity_code.upper()) if raw.primary_commodity_code else None

                dataset_obj, _ = DatasetMaster.objects.update_or_create(
                    code=raw.code,
                    defaults={
                        "name": raw.name,
                        "description": raw.description,
                        "domain": domain,
                        "primary_commodity": primary_commodity,
                        "exchange": exchange,
                        "frequency": frequency,
                        "data_category": getattr(DataCategory, raw.data_category, DataCategory.MARKET_PRICES),
                        "update_cadence": getattr(UpdateCadence, raw.update_cadence, UpdateCadence.DAILY_EOD),
                        "ingestion_mode": getattr(IngestionMode, raw.ingestion_mode, IngestionMode.PULL_SCHEDULED_BATCH),
                        "release_schedule": raw.release_schedule,
                        "retention_policy": getattr(RetentionPolicy, raw.retention_policy, RetentionPolicy.INDEFINITE_POINT_IN_TIME),
                        "license_type": getattr(LicenseType, raw.license_type, LicenseType.PUBLIC_DOMAIN),
                        "point_in_time_enabled": raw.point_in_time_enabled,
                        "supports_revisions": raw.supports_revisions,
                        "sla_max_delay_minutes": raw.sla_max_delay_minutes,
                        "source_authority": raw.source_authority,
                        "documentation_url": raw.documentation_url,
                        "display_order": raw.display_order,
                        "is_active": True,
                    },
                )

                # Link covered commodities (ManyToMany)
                if raw.commodity_codes:
                    linked_comms = [
                        commodities[c.upper()]
                        for c in raw.commodity_codes
                        if c.upper() in commodities
                    ]
                    dataset_obj.commodities.set(linked_comms)
                elif primary_commodity:
                    dataset_obj.commodities.set([primary_commodity])

                datasets_seeded += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {datasets_seeded} dataset master records.")
        )
