"""
Comprehensive test suite for Phase 8: Provider / Source Master.

Covers:
- ProviderMaster model constraints, enums, defaults, and relationships.
- Fallback provider self-referential linking and resolution.
- 12-Factor security guarantee (environment variable mapping; no plaintext keys).
- Pluggable provider architecture (BaseProviderCatalogProvider, StaticProviderCatalogProvider, factory).
- Idempotent database seeder (seed_providers).
- REST API list, retrieve by code/UUID, filters, and summary metrics.
"""

from decimal import Decimal
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.providers.models import AuthType, ProviderMaster, ProviderType
from apps.providers.providers.base import BaseProviderCatalogProvider, RawProviderSpec
from apps.providers.providers.factory import get_provider_catalog
from apps.providers.providers.static_catalog import StaticProviderCatalogProvider


@pytest.mark.django_db
class TestProviderMasterModels:
    """Unit tests for ProviderMaster model definitions and behavior."""

    def test_create_provider_master(self):
        provider = ProviderMaster.objects.create(
            code="CUSTOM_PRA",
            name="Custom Price Reporting Agency",
            description="Specialized assessment agency for biofuels.",
            provider_type=ProviderType.PRICE_REPORTING_AGENCY,
            base_url="https://api.custompra.com/v1/",
            documentation_url="https://custompra.com/docs",
            support_contact="api@custompra.com",
            auth_type=AuthType.BEARER_TOKEN,
            env_var_name="CUSTOM_PRA_TOKEN",
            auth_param_name="Authorization",
            rate_limit_requests=100,
            rate_limit_window_seconds=60,
            backoff_seconds=45,
            target_sla_pct=Decimal("99.90"),
        )
        assert provider.id is not None
        assert provider.code == "CUSTOM_PRA"
        assert provider.auth_type == AuthType.BEARER_TOKEN
        assert provider.has_rate_limit is True
        assert provider.requires_auth is True
        assert "CUSTOM_PRA" in str(provider)

    def test_fallback_provider_relationship(self):
        primary = ProviderMaster.objects.create(
            code="PRIMARY_FEED",
            name="Primary Market Feed",
            provider_type=ProviderType.EXCHANGE_DIRECT,
            base_url="https://primary.example.com",
        )
        backup = ProviderMaster.objects.create(
            code="BACKUP_FEED",
            name="Backup Market Feed",
            provider_type=ProviderType.COMMERCIAL_AGGREGATOR,
            base_url="https://backup.example.com",
        )
        primary.fallback_provider = backup
        primary.save()

        primary.refresh_from_db()
        assert primary.fallback_provider == backup
        assert primary in backup.fallback_for.all()

    def test_unmetered_and_public_provider(self):
        public_provider = ProviderMaster.objects.create(
            code="OPEN_STATS",
            name="Open Government Statistics",
            provider_type=ProviderType.GOVERNMENT_PUBLIC,
            base_url="https://open.gov/api/",
            auth_type=AuthType.NONE_PUBLIC,
            rate_limit_requests=None,
        )
        assert public_provider.has_rate_limit is False
        assert public_provider.requires_auth is False


@pytest.mark.django_db
class TestProviderProviders:
    """Tests for pluggable provider architecture and catalog factory."""

    def test_static_provider_implements_interface(self):
        provider = StaticProviderCatalogProvider()
        assert isinstance(provider, BaseProviderCatalogProvider)

        providers = provider.get_providers()
        assert len(providers) == 20

        # Check key institutional benchmarks
        eia = provider.get_provider("EIA_GOV")
        assert eia is not None
        assert isinstance(eia, RawProviderSpec)
        assert eia.provider_type == "GOVERNMENT_PUBLIC"
        assert eia.env_var_name == "EIA_API_KEY"

        cme = provider.get_provider("CME_DATAMINE")
        assert cme is not None
        assert cme.fallback_code == "ICE_DATA_SERVICES"

    def test_factory_returns_configured_provider(self):
        catalog = get_provider_catalog()
        assert isinstance(catalog, StaticProviderCatalogProvider)


@pytest.mark.django_db
class TestSeedProvidersCommand:
    """Tests for idempotent seed_providers management command."""

    def test_seed_providers_idempotency(self):
        call_command("seed_providers")
        initial_count = ProviderMaster.objects.count()
        assert initial_count == 20

        # Verify fallback linking
        cme = ProviderMaster.objects.get(code="CME_DATAMINE")
        assert cme.fallback_provider is not None
        assert cme.fallback_provider.code == "ICE_DATA_SERVICES"

        # Re-run seeder: ensure zero duplicates
        call_command("seed_providers")
        assert ProviderMaster.objects.count() == initial_count

    def test_seed_providers_clear_flag(self):
        call_command("seed_providers")
        assert ProviderMaster.objects.count() == 20

        call_command("seed_providers", clear=True)
        assert ProviderMaster.objects.count() == 20


@pytest.mark.django_db
class TestProviderAPI:
    """Integration tests for Provider Master REST API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_catalog(self):
        call_command("seed_providers")
        self.client = APIClient()

    def test_list_providers(self):
        response = self.client.get("/api/providers/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 20
        first = data[0]
        assert "code" in first
        assert "provider_type" in first
        assert "auth_type" in first
        assert "rate_limit_requests" in first

    def test_retrieve_provider_by_code(self):
        response = self.client.get("/api/providers/EIA_GOV/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "EIA_GOV"
        assert data["name"] == "U.S. Energy Information Administration"
        assert data["env_var_name"] == "EIA_API_KEY"
        assert "support_contact" in data

    def test_retrieve_provider_by_uuid(self):
        provider = ProviderMaster.objects.get(code="CME_DATAMINE")
        response = self.client.get(f"/api/providers/{provider.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "CME_DATAMINE"
        assert data["fallback_provider_code"] == "ICE_DATA_SERVICES"

    def test_filter_by_provider_type(self):
        response = self.client.get("/api/providers/?provider_type=GOVERNMENT_PUBLIC")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 6
        for item in data:
            assert item["provider_type"] == "GOVERNMENT_PUBLIC"

    def test_filter_by_auth_type(self):
        response = self.client.get("/api/providers/?auth_type=BEARER_TOKEN")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert item["auth_type"] == "BEARER_TOKEN"

    def test_filter_by_has_rate_limit(self):
        response = self.client.get("/api/providers/?has_rate_limit=true")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert item["rate_limit_requests"] is not None

    def test_search_providers(self):
        response = self.client.get("/api/providers/?search=Petroleum")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        codes = [item["code"] for item in data]
        assert "EIA_GOV" in codes

    def test_providers_summary_metrics(self):
        response = self.client.get("/api/providers/summary/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_providers"] == 20
        assert data["active_providers"] == 20
        assert data["with_rate_limits"] >= 19
        assert data["with_fallbacks"] >= 6
        assert "GOVERNMENT_PUBLIC" in data["by_provider_type"]
        assert "API_KEY_QUERY_PARAM" in data["by_auth_type"]
