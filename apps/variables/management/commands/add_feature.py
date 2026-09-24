"""
Management command to quickly and declaratively onboard a new feature into the system.

Eliminates manual multi-table boilerplate by atomically creating or linking:
1. ProviderMaster (WHO provides the data)
2. DatasetMaster (WHAT report/dataset contains it)
3. EndpointMaster (WHERE to fetch it via API)
4. VariableMaster (WHICH standardized metric it represents)

Can be run via CLI flags or by passing a JSON specification file.
"""

import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.commodities.models import CommodityMaster
from apps.datasets.models import DataCategory, DatasetMaster, IngestionMode, UpdateCadence
from apps.endpoints.models import EndpointMaster, HttpMethod, ProtocolType, ResponseFormat
from apps.metadata.models import DataDomainMaster, FrequencyMaster, UnitMaster
from apps.providers.models import AuthType, ProviderMaster, ProviderType
from apps.variables.models import AggregationMethod, DisplayTransformation, VariableDataType, VariableMaster


class Command(BaseCommand):
    help = "Quickly register a new quantitative feature, metric, dataset, and endpoint into the catalog."

    def add_arguments(self, parser):
        parser.add_argument("--code", type=str, help="Canonical variable/feature code (e.g. 'EU_GAS_STORAGE_TWH')")
        parser.add_argument("--name", type=str, help="Human-readable title (e.g. 'European Working Gas Storage')")
        parser.add_argument("--unit", type=str, default="BCF", help="Canonical Unit of Measure code (e.g. 'MBBL', 'BCF', 'MT')")
        parser.add_argument("--domain", type=str, default="INVENTORIES", help="Data Domain code (e.g. 'INVENTORIES', 'FUTURES_PRICES')")
        parser.add_argument("--commodity", type=str, default="", help="Optional commodity code anchor (e.g. 'CL', 'NG')")
        parser.add_argument("--dataset", type=str, default="", help="Dataset code. Will create if doesn't exist.")
        parser.add_argument("--provider", type=str, default="", help="Provider code. Will create if doesn't exist.")
        parser.add_argument("--endpoint-path", type=str, default="", help="Endpoint path template (e.g. 'api/v1/storage')")
        parser.add_argument("--json-file", type=str, default="", help="Path to a JSON file containing a feature declaration")

    def handle(self, *args, **options):
        json_path = options.get("json_file")
        if json_path:
            p = Path(json_path)
            if not p.exists():
                self.stderr.write(self.style.ERROR(f"JSON file not found: {json_path}"))
                return
            with open(p, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self._register_feature(payload)
            return

        code = options.get("code")
        if not code:
            self.stderr.write(self.style.ERROR("Error: --code or --json-file is required. Run with --help for usage."))
            return

        payload = {
            "code": code.upper().strip(),
            "name": options.get("name") or code.replace("_", " ").title(),
            "unit": (options.get("unit") or "MBBL").upper().strip(),
            "domain": (options.get("domain") or "INVENTORIES").upper().strip(),
            "commodity": options.get("commodity", "").upper().strip(),
            "dataset": (options.get("dataset") or f"{code}_DATASET").upper().strip(),
            "provider": (options.get("provider") or "GENERIC_PROVIDER").upper().strip(),
            "endpoint_path": options.get("endpoint_path", f"data/{code.lower()}"),
        }
        self._register_feature(payload)

    def _register_feature(self, data: dict):
        var_code = data["code"]
        name = data.get("name", var_code.replace("_", " ").title())
        unit_code = data.get("unit", "MBBL")
        domain_code = data.get("domain", "INVENTORIES")
        comm_code = data.get("commodity", "")
        dataset_code = data.get("dataset", f"{var_code}_DATASET")
        provider_code = data.get("provider", "GENERIC_PROVIDER")
        endpoint_path = data.get("endpoint_path", f"data/{var_code.lower()}")

        with transaction.atomic():
            # 1. Resolve or create Unit & Domain
            unit = UnitMaster.objects.filter(code=unit_code).first()
            if not unit:
                unit = UnitMaster.objects.first()
                self.stdout.write(self.style.WARNING(f"Unit '{unit_code}' not found. Defaulted to '{unit.code}'."))

            domain = DataDomainMaster.objects.filter(code=domain_code).first()
            if not domain:
                domain = DataDomainMaster.objects.filter(category="PHYSICAL").first() or DataDomainMaster.objects.first()
                self.stdout.write(self.style.WARNING(f"Domain '{domain_code}' not found. Defaulted to '{domain.code}'."))

            # 2. Resolve optional Commodity
            commodity = CommodityMaster.objects.filter(code=comm_code).first() if comm_code else None

            # 3. Resolve or create Provider
            provider, p_created = ProviderMaster.objects.get_or_create(
                code=provider_code,
                defaults={
                    "name": data.get("provider_name", f"{provider_code} Data Source"),
                    "provider_type": ProviderType.GOVERNMENT_PUBLIC,
                    "base_url": data.get("base_url", "https://api.source.org/v1/"),
                    "auth_type": AuthType.NONE_PUBLIC,
                },
            )
            if p_created:
                self.stdout.write(f"  + Created ProviderMaster: '{provider.code}'")

            # 4. Resolve or create Dataset
            freq = FrequencyMaster.objects.filter(code="DAILY").first() or FrequencyMaster.objects.first()
            dataset, d_created = DatasetMaster.objects.get_or_create(
                code=dataset_code,
                defaults={
                    "name": data.get("dataset_name", f"{dataset_code} Dataset"),
                    "domain": domain,
                    "frequency": freq,
                    "source_authority": provider.name,
                    "data_category": DataCategory.INVENTORIES_STOCKS,
                    "update_cadence": UpdateCadence.WEEKLY_FIXED_DAY,
                    "ingestion_mode": IngestionMode.PULL_SCHEDULED_BATCH,
                },
            )
            if d_created:
                self.stdout.write(f"  + Created DatasetMaster: '{dataset.code}'")

            # 5. Resolve or create Endpoint
            endpoint_code = data.get("endpoint_code", f"{dataset_code}_FEED")
            endpoint, ep_created = EndpointMaster.objects.get_or_create(
                code=endpoint_code,
                defaults={
                    "name": f"{dataset.name} Endpoint",
                    "provider": provider,
                    "dataset": dataset,
                    "protocol": ProtocolType.REST_HTTP,
                    "http_method": HttpMethod.GET,
                    "path_template": endpoint_path,
                    "response_format": ResponseFormat.JSON,
                    "data_envelope_path": data.get("envelope_path", ""),
                },
            )
            if ep_created:
                self.stdout.write(f"  + Created EndpointMaster: '{endpoint.code}' ({endpoint.path_template})")

            # 6. Create or update VariableMaster
            var, v_created = VariableMaster.objects.update_or_create(
                code=var_code,
                defaults={
                    "name": name,
                    "description": data.get("description", f"Observable feature: {name}"),
                    "dataset": dataset,
                    "domain": domain,
                    "commodity": commodity,
                    "unit": unit,
                    "data_type": VariableDataType.DECIMAL,
                    "aggregation_method": AggregationMethod.LAST,
                    "default_transformation": DisplayTransformation.RAW_LEVEL,
                    "is_benchmark": data.get("is_benchmark", True),
                    "is_active": True,
                },
            )
            action = "Created" if v_created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"[SUCCESS] {action} Feature Variable '{var.code}' -> Linked to Dataset '{dataset.code}' & Provider '{provider.code}'."
                )
            )
