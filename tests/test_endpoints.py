"""
Comprehensive test suite for Phase 9: Endpoint & API Metadata subsystem.

Covers:
- EndpointMaster model constraints, enums, defaults, and relationships.
- URL joining and formatting logic (get_full_url).
- Request parameter builder with runtime overrides (build_request_params).
- Pluggable provider architecture (BaseEndpointCatalogProvider, StaticEndpointCatalogProvider, factory).
- Idempotent database seeder (seed_endpoints).
- REST API list, retrieve by code/UUID, query filters, and summary metrics.
"""

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.datasets.models import DatasetMaster
from apps.endpoints.models import EndpointMaster, HttpMethod, ProtocolType, ResponseFormat
from apps.endpoints.providers.base import BaseEndpointCatalogProvider, RawEndpointSpec
from apps.endpoints.providers.factory import get_endpoint_catalog
from apps.endpoints.providers.static_catalog import StaticEndpointCatalogProvider
from apps.providers.models import AuthType, ProviderMaster, ProviderType


@pytest.mark.django_db
class TestEndpointMasterModels:
    """Unit tests for EndpointMaster model definitions and behavior."""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        call_command("seed_metadata")
        call_command("seed_datasets")
        self.provider = ProviderMaster.objects.create(
            code="TEST_PROVIDER",
            name="Test Market Provider",
            provider_type=ProviderType.COMMERCIAL_AGGREGATOR,
            base_url="https://api.testprovider.com/v2/",
            auth_type=AuthType.API_KEY_QUERY_PARAM,
            auth_param_name="api_key",
        )
        self.dataset = DatasetMaster.objects.first()

    def test_create_endpoint_master(self):
        endpoint = EndpointMaster.objects.create(
            code="TEST_CRUDE_INVENTORIES",
            name="Test Weekly Crude Stocks",
            description="Weekly crude inventory endpoint.",
            provider=self.provider,
            dataset=self.dataset,
            protocol=ProtocolType.REST_HTTP,
            http_method=HttpMethod.GET,
            path_template="petroleum/stocks/crude",
            response_format=ResponseFormat.JSON,
            data_envelope_path="response.data",
            default_params={"frequency": "weekly", "units": "barrels"},
            custom_headers={"Accept": "application/json"},
            cache_ttl_seconds=1800,
        )

        assert endpoint.id is not None
        assert endpoint.code == "TEST_CRUDE_INVENTORIES"
        assert endpoint.provider == self.provider
        assert endpoint.dataset == self.dataset
        assert endpoint.protocol == ProtocolType.REST_HTTP
        assert endpoint.http_method == HttpMethod.GET
        assert endpoint.response_format == ResponseFormat.JSON
        assert "TEST_CRUDE_INVENTORIES" in str(endpoint)

    def test_get_full_url_slashes_and_formatting(self):
        endpoint = EndpointMaster.objects.create(
            code="TEST_URL_GEN",
            name="Test URL Generation",
            provider=self.provider,
            path_template="/market/series/{symbol}/eod",
        )

        # Basic path join with slash normalization
        url = endpoint.get_full_url(symbol="CL")
        assert url == "https://api.testprovider.com/v2/market/series/CL/eod"

        # Provider without trailing slash
        self.provider.base_url = "https://api.testprovider.com/v2"
        self.provider.save()
        url2 = endpoint.get_full_url(symbol="NG")
        assert url2 == "https://api.testprovider.com/v2/market/series/NG/eod"

    def test_build_request_params(self):
        endpoint = EndpointMaster.objects.create(
            code="TEST_PARAMS",
            name="Test Parameters Builder",
            provider=self.provider,
            path_template="data",
            default_params={"limit": 50, "sort": "desc"},
        )

        merged = endpoint.build_request_params({"limit": 100, "date": "2026-09-23"})
        assert merged["limit"] == 100
        assert merged["sort"] == "desc"
        assert merged["date"] == "2026-09-23"

    def test_endpoint_without_dataset(self):
        endpoint = EndpointMaster.objects.create(
            code="TEST_NO_DATASET",
            name="Discovery Metadata Endpoint",
            provider=self.provider,
            path_template="metadata/routes",
            dataset=None,
        )
        assert endpoint.dataset is None
        assert endpoint.provider == self.provider


@pytest.mark.django_db
class TestEndpointProviders:
    """Tests for pluggable endpoint catalog provider architecture."""

    def test_static_provider_implements_interface(self):
        provider = StaticEndpointCatalogProvider()
        assert isinstance(provider, BaseEndpointCatalogProvider)

        endpoints = provider.get_endpoints()
        assert len(endpoints) >= 25

        # Check key benchmark endpoints
        eia = provider.get_endpoint("EIA_PETROLEUM_SPOT_PRICES")
        assert eia is not None
        assert isinstance(eia, RawEndpointSpec)
        assert eia.provider_code == "EIA_GOV"
        assert eia.dataset_code == "EIA_WPSR_PETROLEUM_STOCKS"
        assert eia.response_format == "JSON"

        cftc = provider.get_endpoint("CFTC_COT_DISAGGREGATED_FUT")
        assert cftc is not None
        assert cftc.provider_code == "CFTC_GOV"
        assert cftc.response_format == "JSON"

    def test_factory_returns_configured_provider(self):
        catalog = get_endpoint_catalog()
        assert isinstance(catalog, StaticEndpointCatalogProvider)


@pytest.mark.django_db
class TestSeedEndpointsCommand:
    """Tests for idempotent seed_endpoints management command."""

    @pytest.fixture(autouse=True)
    def setup_prerequisites(self):
        call_command("seed_metadata")
        call_command("seed_providers")
        call_command("seed_datasets")

    def test_seed_endpoints_idempotency(self):
        call_command("seed_endpoints")
        initial_count = EndpointMaster.objects.count()
        assert initial_count >= 25

        # Re-run seeder: ensure zero duplicates
        call_command("seed_endpoints")
        assert EndpointMaster.objects.count() == initial_count

    def test_seed_endpoints_clear_flag(self):
        call_command("seed_endpoints")
        count_before = EndpointMaster.objects.count()
        assert count_before >= 25

        call_command("seed_endpoints", clear=True)
        assert EndpointMaster.objects.count() == count_before


@pytest.mark.django_db
class TestEndpointAPI:
    """Integration tests for Endpoint Master REST API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_catalog(self):
        call_command("seed_metadata")
        call_command("seed_providers")
        call_command("seed_datasets")
        call_command("seed_endpoints")
        self.client = APIClient()

    def test_list_endpoints(self):
        response = self.client.get("/api/endpoints/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 25

        first = data[0]
        assert "code" in first
        assert "provider_code" in first
        assert "protocol" in first
        assert "http_method" in first
        assert "full_url" in first
        assert "response_format" in first

    def test_retrieve_endpoint_by_code(self):
        response = self.client.get("/api/endpoints/EIA_PETROLEUM_SPOT_PRICES/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "EIA_PETROLEUM_SPOT_PRICES"
        assert data["provider_code"] == "EIA_GOV"
        assert data["dataset_code"] == "EIA_WPSR_PETROLEUM_STOCKS"
        assert data["http_method"] == "GET"
        assert "api.eia.gov" in data["full_url"]
        assert "default_params" in data
        assert "data_envelope_path" in data

    def test_retrieve_endpoint_by_uuid(self):
        endpoint = EndpointMaster.objects.get(code="FRED_SERIES_OBSERVATIONS")
        response = self.client.get(f"/api/endpoints/{endpoint.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "FRED_SERIES_OBSERVATIONS"
        assert data["provider_code"] == "FRED_FED"

    def test_filter_by_provider(self):
        response = self.client.get("/api/endpoints/?provider=EIA_GOV")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        for item in data:
            assert item["provider_code"] == "EIA_GOV"

    def test_filter_by_protocol(self):
        response = self.client.get("/api/endpoints/?protocol=REST_HTTP")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for item in data:
            assert item["protocol"] == "REST_HTTP"

    def test_filter_by_http_method(self):
        response = self.client.get("/api/endpoints/?http_method=GET")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for item in data:
            assert item["http_method"] == "GET"

    def test_filter_by_response_format(self):
        response = self.client.get("/api/endpoints/?response_format=JSON")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for item in data:
            assert item["response_format"] == "JSON"

    def test_search_endpoints(self):
        response = self.client.get("/api/endpoints/?search=Crude")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_endpoints_summary_metrics(self):
        response = self.client.get("/api/endpoints/summary/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_endpoints"] >= 25
        assert data["active_endpoints"] >= 25
        assert "REST_HTTP" in data["by_protocol"]
        assert "GET" in data["by_http_method"]
        assert "JSON" in data["by_response_format"]
        assert "EIA_GOV" in data["by_provider"]
