"""
Management command to seed canonical commodity market variables.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.commodities.models import CommodityMaster
from apps.datasets.models import DatasetMaster
from apps.metadata.models import DataDomainMaster, UnitMaster
from apps.variables.models import VariableMaster
from apps.variables.providers.factory import get_variable_provider


class Command(BaseCommand):
    help = "Seeds canonical standardized variables, metrics, units, and aggregation rules into VariableMaster."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding canonical Variable Master catalog..."))

        provider = get_variable_provider()
        specs = provider.get_variables()

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for spec in specs:
                dataset = DatasetMaster.objects.filter(code=spec.dataset_code).first()
                if not dataset:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Dataset '{spec.dataset_code}' not found for variable '{spec.code}'. Skipping."
                        )
                    )
                    skipped_count += 1
                    continue

                domain = DataDomainMaster.objects.filter(code=spec.domain_code).first()
                if not domain:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Domain '{spec.domain_code}' not found for variable '{spec.code}'. Skipping."
                        )
                    )
                    skipped_count += 1
                    continue

                unit = UnitMaster.objects.filter(code=spec.unit_code).first()
                if not unit:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Unit '{spec.unit_code}' not found for variable '{spec.code}'. Skipping."
                        )
                    )
                    skipped_count += 1
                    continue

                commodity = None
                if spec.commodity_code:
                    commodity = CommodityMaster.objects.filter(code=spec.commodity_code).first()

                var_obj, created = VariableMaster.objects.update_or_create(
                    code=spec.code,
                    defaults={
                        "name": spec.name,
                        "description": spec.description,
                        "dataset": dataset,
                        "domain": domain,
                        "commodity": commodity,
                        "unit": unit,
                        "data_type": spec.data_type,
                        "aggregation_method": spec.aggregation_method,
                        "seasonal_adjustment": spec.seasonal_adjustment,
                        "default_transformation": spec.default_transformation,
                        "is_benchmark": spec.is_benchmark,
                        "is_active": True,
                        "display_order": spec.display_order,
                    },
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded Variable Master: {created_count} created, "
                f"{updated_count} updated, {skipped_count} skipped (Total: {VariableMaster.objects.count()})."
            )
        )
