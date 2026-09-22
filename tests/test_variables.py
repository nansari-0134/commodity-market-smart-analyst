"""
Tests for Phase 7: Variable Master catalog, providers, management commands, and REST APIs.
"""

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.commodities.models import CommodityMaster
from apps.datasets.models import DatasetMaster
from apps.metadata.models import DataDomainMaster, UnitMaster
from apps.variables.models import (
    AggregationMethod,
    DisplayTransformation,
    SeasonalAdjustment,
    VariableDataType,
    VariableMaster,
)
from apps.variables.providers.base import BaseVariableCatalogProvider, RawVariableSpec
from apps.variables.providers.factory import get_variable_provider
from apps.variables.providers.static_catalog import StaticVariableCatalogProvider


@pytest.mark.django_db
class TestVariableMasterModels:
    """Test VariableMaster model creation, constraints, relationships, and string representations."""

    def test_create_variable_master(self):
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")
        call_command("seed_datasets")

        dataset = DatasetMaster.objects.first()
        domain = DataDomainMaster.objects.first()
        unit = UnitMaster.objects.first()
        cl = CommodityMaster.objects.filter(code="CL").first()

        var = VariableMaster.objects.create(
            code="TEST_CUSHING_INVENTORY",
            name="Test Cushing Inventory Level",
            description="Testing variable creation",
            dataset=dataset,
            domain=domain,
            commodity=cl,
            unit=unit,
            data_type=VariableDataType.DECIMAL,
            aggregation_method=AggregationMethod.LAST,
            seasonal_adjustment=SeasonalAdjustment.UNADJUSTED,
            default_transformation=DisplayTransformation.DIFF_1W,
            is_benchmark=True,
        )

        assert str(var) == f"TEST_CUSHING_INVENTORY: Test Cushing Inventory Level [CL] ({unit.code})"
        assert var.id is not None
        assert var.is_benchmark is True
        assert var.aggregation_method == AggregationMethod.LAST

    def test_variable_relationships_and_reverse_queries(self):
        """Test dataset, commodity, and unit reverse lookups."""
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")
        call_command("seed_datasets")

        dataset = DatasetMaster.objects.filter(code="EIA_WPSR_PETROLEUM_STOCKS").first()
        domain = DataDomainMaster.objects.filter(code="INVENTORIES").first()
        unit = UnitMaster.objects.filter(code="MBBL").first()
        cl = CommodityMaster.objects.filter(code="CL").first()

        var = VariableMaster.objects.create(
            code="TEST_REV_VAR",
            name="Test Reverse Query Variable",
            dataset=dataset,
            domain=domain,
            commodity=cl,
            unit=unit,
        )

        # Verify forward
        assert var.dataset == dataset
        assert var.commodity == cl
        assert var.unit == unit

        # Verify reverse
        assert var in dataset.variables.all()
        assert var in cl.variables.all()
        assert var in unit.variables.all()
        assert var in domain.variables.all()


@pytest.mark.django_db
class TestVariableProviders:
    """Test pluggable provider interface and static variable catalog."""

    def test_static_provider_implements_interface(self):
        provider = StaticVariableCatalogProvider()
        assert isinstance(provider, BaseVariableCatalogProvider)

        catalog = provider.get_variables()
        assert len(catalog) >= 35
        for item in catalog:
            assert isinstance(item, RawVariableSpec)
            assert item.code
            assert item.name
            assert item.dataset_code
            assert item.domain_code
            assert item.unit_code

    def test_factory_returns_configured_provider(self):
        provider = get_variable_provider()
        assert isinstance(provider, BaseVariableCatalogProvider)


@pytest.mark.django_db
class TestSeedVariablesCommand:
    """Test the seed_variables management command idempotency."""

    def test_seed_variables_idempotency(self):
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")
        call_command("seed_datasets")

        # Run seeder first time
        call_command("seed_variables")
        initial_count = VariableMaster.objects.count()
        assert initial_count >= 35

        # Run seeder second time (must not duplicate rows)
        call_command("seed_variables")
        second_count = VariableMaster.objects.count()
        assert second_count == initial_count


@pytest.mark.django_db
class TestVariableAPI:
    """Test REST API endpoints for Variable Master catalog."""

    @pytest.fixture(autouse=True)
    def setup_catalog(self):
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")
        call_command("seed_datasets")
        call_command("seed_variables")
        self.client = APIClient()

    def test_list_variables(self):
        response = self.client.get("/api/variables/")
        assert response.status_code == 200
        assert len(response.data) >= 35

    def test_retrieve_variable_by_code(self):
        response = self.client.get("/api/variables/CRUDE_CUSHING_STOCKS/")
        assert response.status_code == 200
        data = response.data
        assert data["code"] == "CRUDE_CUSHING_STOCKS"
        assert data["dataset_code"] == "EIA_WPSR_PETROLEUM_STOCKS"
        assert data["commodity_code"] == "CL"
        assert data["aggregation_method"] == "LAST"
        assert data["is_benchmark"] is True

    def test_filter_by_commodity(self):
        response = self.client.get("/api/variables/", {"commodity": "CL"})
        assert response.status_code == 200
        assert len(response.data) > 0
        for v in response.data:
            assert v["commodity_code"] == "CL"

    def test_filter_by_dataset(self):
        response = self.client.get("/api/variables/", {"dataset": "USDA_WASDE_WORLD_GRAINS"})
        assert response.status_code == 200
        assert len(response.data) > 0
        for v in response.data:
            assert v["dataset_code"] == "USDA_WASDE_WORLD_GRAINS"

    def test_filter_by_benchmark(self):
        response = self.client.get("/api/variables/", {"is_benchmark": "true"})
        assert response.status_code == 200
        assert len(response.data) > 0
        for v in response.data:
            assert v["is_benchmark"] is True

    def test_filter_by_aggregation_method(self):
        response = self.client.get("/api/variables/", {"aggregation_method": "SUM"})
        assert response.status_code == 200
        assert len(response.data) > 0
        for v in response.data:
            assert v["aggregation_method"] == "SUM"

    def test_search_variables(self):
        response = self.client.get("/api/variables/", {"search": "Cushing"})
        assert response.status_code == 200
        assert len(response.data) > 0

    def test_variables_summary_metrics(self):
        response = self.client.get("/api/variables/summary/")
        assert response.status_code == 200
        summary = response.data
        assert summary["total_variables"] >= 35
        assert summary["active_variables"] >= 35
        assert summary["benchmark_variables"] >= 20
        assert "by_data_type" in summary
        assert "by_aggregation_method" in summary
        assert "by_domain" in summary
        assert "by_dataset" in summary
