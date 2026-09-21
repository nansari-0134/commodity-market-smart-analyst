"""
Tests for Phase 6: Dataset Master catalog, providers, management commands, and REST APIs.
"""

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.commodities.models import CommodityMaster
from apps.datasets.models import (
    DataCategory,
    DatasetMaster,
    IngestionMode,
    LicenseType,
    RetentionPolicy,
    UpdateCadence,
)
from apps.datasets.providers.base import BaseDatasetCatalogProvider, RawDatasetSpec
from apps.datasets.providers.factory import get_dataset_provider
from apps.datasets.providers.static_catalog import StaticDatasetCatalogProvider
from apps.metadata.models import DataDomainMaster, FrequencyMaster


@pytest.mark.django_db
class TestDatasetMasterModels:
    """Test DatasetMaster model creation, constraints, relationships, and string representations."""

    def test_create_dataset_master(self):
        domain = DataDomainMaster.objects.first()
        if not domain:
            call_command("seed_metadata")
            domain = DataDomainMaster.objects.first()

        freq = FrequencyMaster.objects.first()

        dataset = DatasetMaster.objects.create(
            code="TEST_SERIES_01",
            name="Test Market Series",
            description="Testing dataset catalog model",
            domain=domain,
            frequency=freq,
            data_category=DataCategory.MARKET_PRICES,
            update_cadence=UpdateCadence.DAILY_EOD,
            ingestion_mode=IngestionMode.PULL_SCHEDULED_BATCH,
            retention_policy=RetentionPolicy.INDEFINITE_POINT_IN_TIME,
            license_type=LicenseType.PUBLIC_DOMAIN,
            source_authority="Test Agency",
            sla_max_delay_minutes=30,
        )

        assert str(dataset) == "TEST_SERIES_01: Test Market Series (Test Agency)"
        assert dataset.id is not None
        assert dataset.point_in_time_enabled is True
        assert dataset.supports_revisions is True
        assert dataset.sla_max_delay_minutes == 30

    def test_dataset_commodity_relationships(self):
        """Test primary commodity FK and multi-commodity ManyToMany relationships."""
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")

        domain = DataDomainMaster.objects.first()
        freq = FrequencyMaster.objects.first()
        cl = CommodityMaster.objects.filter(code="CL").first()
        brent = CommodityMaster.objects.filter(code="BRENT").first()
        ng = CommodityMaster.objects.filter(code="NG").first()

        dataset = DatasetMaster.objects.create(
            code="MULTI_ENERGY_WEEKLY",
            name="Multi Energy Weekly Stocks",
            domain=domain,
            frequency=freq,
            primary_commodity=cl,
            data_category=DataCategory.INVENTORIES_STOCKS,
            source_authority="Energy Authority",
        )
        dataset.commodities.add(cl, brent, ng)

        assert dataset.primary_commodity == cl
        assert dataset.commodities.count() == 3
        assert cl in dataset.commodities.all()
        assert brent in dataset.commodities.all()

        # Reverse relation
        assert dataset in cl.datasets.all()


@pytest.mark.django_db
class TestDatasetProviders:
    """Test pluggable provider interface and static dataset catalog."""

    def test_static_provider_implements_interface(self):
        provider = StaticDatasetCatalogProvider()
        assert isinstance(provider, BaseDatasetCatalogProvider)

        catalog = provider.get_datasets()
        assert len(catalog) >= 20
        for item in catalog:
            assert isinstance(item, RawDatasetSpec)
            assert item.code
            assert item.name
            assert item.domain_code
            assert item.frequency_code
            assert item.source_authority

    def test_factory_returns_configured_provider(self):
        provider = get_dataset_provider()
        assert isinstance(provider, BaseDatasetCatalogProvider)


@pytest.mark.django_db
class TestSeedDatasetsCommand:
    """Test the seed_datasets management command idempotency."""

    def test_seed_datasets_idempotency(self):
        # Initial seed of prerequisites
        call_command("seed_metadata")
        call_command("seed_exchanges")
        call_command("seed_commodities")

        # Run seeder first time
        call_command("seed_datasets")
        initial_count = DatasetMaster.objects.count()
        assert initial_count >= 20

        # Run seeder second time (must not duplicate or crash)
        call_command("seed_datasets")
        second_count = DatasetMaster.objects.count()
        assert second_count == initial_count


@pytest.mark.django_db
class TestDatasetAPI:
    """Test REST API endpoints for Dataset Master catalog."""

    @pytest.fixture(autouse=True)
    def setup_catalog(self):
        call_command("seed_metadata")
        call_command("seed_exchanges", skip_api_holidays=True)
        call_command("seed_commodities")
        call_command("seed_datasets")
        self.client = APIClient()

    def test_list_datasets(self):
        response = self.client.get("/api/datasets/")
        assert response.status_code == 200
        assert len(response.data) >= 20

    def test_retrieve_dataset_by_code(self):
        response = self.client.get("/api/datasets/CME_FUTURES_EOD/")
        assert response.status_code == 200
        data = response.data
        assert data["code"] == "CME_FUTURES_EOD"
        assert "domain_code" in data
        assert "update_cadence" in data
        assert "source_authority" in data
        assert isinstance(data["covered_commodities"], list)

    def test_filter_by_category(self):
        response = self.client.get("/api/datasets/", {"category": "SUPPLY_DEMAND"})
        assert response.status_code == 200
        for ds in response.data:
            assert ds["data_category"] == "SUPPLY_DEMAND"

    def test_filter_by_commodity(self):
        # Corn is linked in multi-asset agricultural datasets
        response = self.client.get("/api/datasets/", {"commodity": "CORN"})
        assert response.status_code == 200
        assert len(response.data) > 0
        codes = [d["code"] for d in response.data]
        assert "USDA_WASDE_WORLD_GRAINS" in codes

    def test_search_datasets(self):
        response = self.client.get("/api/datasets/", {"search": "Petroleum"})
        assert response.status_code == 200
        assert len(response.data) > 0

    def test_datasets_summary_metrics(self):
        response = self.client.get("/api/datasets/summary/")
        assert response.status_code == 200
        summary = response.data
        assert summary["total_datasets"] >= 20
        assert "category_breakdown" in summary
        assert "cadence_breakdown" in summary
        assert "ingestion_mode_breakdown" in summary
        assert "license_breakdown" in summary
        assert summary["active_datasets"] >= 20
