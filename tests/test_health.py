"""
Tests for health check endpoints and platform dashboard.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_endpoint(client):
    """Verify the lightweight /health/ endpoint returns HTTP 200 and valid JSON."""
    url = reverse("core:health_check")
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data
    assert data["database"]["status"] == "healthy"
    assert "timestamp_utc" in data


@pytest.mark.django_db
def test_api_health_check_endpoint():
    """Verify the REST /api/health/ endpoint returns HTTP 200 and system details."""
    api_client = APIClient()
    url = reverse("core:api_health_check")
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.data
    assert data["status"] == "online"
    assert data["point_in_time_ready"] is True
    assert data["timezone"] == "UTC"
    assert data["database"]["connected"] is True


@pytest.mark.django_db
def test_dashboard_index_view(client):
    """Verify the main intelligence terminal view renders with HTTP 200."""
    url = reverse("dashboard:index")
    response = client.get(url)
    assert response.status_code == 200
    assert b"Commodity Market Intelligence" in response.content
    assert b"Phase Roadmap" in response.content
    assert b"Quantitative Pipeline" in response.content


@pytest.mark.django_db
def test_dashboard_explorer_view(client):
    """Verify the visual Data Explorer view renders with HTTP 200 and passes catalog metrics."""
    url = reverse("dashboard:explorer")
    response = client.get(url)
    assert response.status_code == 200
    assert b"Institutional Data Explorer" in response.content
    assert "provider_count" in response.context
    assert "variable_count" in response.context
    assert "dataset_count" in response.context
    assert "contract_count" in response.context

    # Verify tab deep-linking parameter
    tab_response = client.get(f"{url}?tab=variables")
    assert tab_response.status_code == 200
    assert tab_response.context["active_tab"] == "variables"

