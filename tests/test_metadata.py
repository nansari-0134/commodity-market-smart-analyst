"""
Automated unit and API tests for Phase 2: Metadata Schema.
"""
from decimal import Decimal
import pytest
from django.urls import reverse
from django.core.management import call_command
from rest_framework.test import APIClient
from apps.metadata.models import (
    DataDomainMaster,
    DataDomainCategory,
    UnitMaster,
    UnitType,
    FrequencyMaster,
)


@pytest.mark.django_db
def test_seed_metadata_command():
    """Verify seed_metadata command runs idempotently and populates canonical metadata."""
    call_command("seed_metadata")
    assert DataDomainMaster.objects.count() >= 33
    assert UnitMaster.objects.count() >= 30
    assert FrequencyMaster.objects.count() >= 12

    # Running a second time should not duplicate records
    call_command("seed_metadata")
    assert DataDomainMaster.objects.count() >= 33


@pytest.mark.django_db
def test_data_domain_hierarchy():
    """Verify parent-child domain relationships and hierarchy_path generation."""
    parent = DataDomainMaster.objects.create(
        code="TEST_PARENT",
        name="Parent Domain",
        category=DataDomainCategory.PHYSICAL,
    )
    child = DataDomainMaster.objects.create(
        code="TEST_CHILD",
        name="Child Domain",
        category=DataDomainCategory.PHYSICAL,
        parent=parent,
    )
    assert child.parent == parent
    assert child.hierarchy_path == "Parent Domain > Child Domain"
    assert parent.subdomains.count() == 1
    assert parent.subdomains.first() == child


@pytest.mark.django_db
def test_unit_conversion_math():
    """Verify mathematical unit conversions to base unit."""
    base_bbl = UnitMaster.objects.create(
        code="TEST_BBL",
        name="Barrels",
        unit_type=UnitType.VOLUME,
        conversion_factor=Decimal("1.0"),
    )
    mbbl = UnitMaster.objects.create(
        code="TEST_MBBL",
        name="Thousand Barrels",
        unit_type=UnitType.VOLUME,
        base_unit=base_bbl,
        conversion_factor=Decimal("1000.0"),
    )
    # 5 MBBL = 5000 BBL
    converted = mbbl.to_base_unit(5)
    assert converted == Decimal("5000.0")

    # Base unit to itself
    assert base_bbl.to_base_unit(10) == Decimal("10")

    # Direct unit-to-unit conversion
    mmbbl = UnitMaster.objects.create(
        code="TEST_MMBBL",
        name="Million Barrels",
        unit_type=UnitType.VOLUME,
        base_unit=base_bbl,
        conversion_factor=Decimal("1000000.0"),
    )
    # 5000 MBBL -> 5 MMBBL
    assert mbbl.convert_to(5000, mmbbl) == Decimal("5.0")
    # 2.5 MMBBL -> 2500 MBBL
    assert mmbbl.convert_to(Decimal("2.5"), mbbl) == Decimal("2500.0")

    # Incompatible unit type error handling (Volume -> Mass)
    mt = UnitMaster.objects.create(
        code="TEST_MT",
        name="Metric Ton",
        unit_type=UnitType.MASS,
        conversion_factor=Decimal("1.0"),
    )
    with pytest.raises(ValueError, match="Cannot convert between incompatible unit types"):
        mbbl.convert_to(100, mt)


@pytest.mark.django_db
def test_frequency_intervals():
    """Verify frequency interval definitions and regular vs irregular classifications."""
    daily = FrequencyMaster.objects.create(
        code="TEST_DAILY",
        name="Daily",
        standard_interval_seconds=86400,
        is_regular=True,
    )
    assert daily.standard_interval_seconds == 86400
    assert daily.is_regular is True

    event = FrequencyMaster.objects.create(
        code="TEST_EVENT",
        name="Event-Driven",
        standard_interval_seconds=None,
        is_regular=False,
    )
    assert event.standard_interval_seconds is None
    assert event.is_regular is False


@pytest.mark.django_db
def test_metadata_api_endpoints():
    """Verify REST API responses for domains, units, frequencies, and summary."""
    call_command("seed_metadata")
    client = APIClient()

    # 1. Domains endpoint
    url_domains = reverse("metadata:domain_list")
    resp_domains = client.get(url_domains)
    assert resp_domains.status_code == 200
    assert len(resp_domains.data) >= 33

    # Top-level filter
    resp_top = client.get(f"{url_domains}?top=true")
    assert resp_top.status_code == 200
    for domain in resp_top.data:
        assert domain["parent"] is None

    # Category filter
    resp_cat = client.get(f"{url_domains}?category=MARKET")
    assert resp_cat.status_code == 200
    for domain in resp_cat.data:
        assert domain["category"] == "MARKET"

    # 2. Units endpoint
    url_units = reverse("metadata:unit_list")
    resp_units = client.get(url_units)
    assert resp_units.status_code == 200
    assert len(resp_units.data) >= 30

    # Type filter
    resp_type = client.get(f"{url_units}?type=VOLUME")
    assert resp_type.status_code == 200
    for unit in resp_type.data:
        assert unit["unit_type"] == "VOLUME"

    # 3. Frequencies endpoint
    url_freq = reverse("metadata:frequency_list")
    resp_freq = client.get(url_freq)
    assert resp_freq.status_code == 200
    assert len(resp_freq.data) >= 12

    # 4. Summary endpoint
    url_sum = reverse("metadata:metadata_summary")
    resp_sum = client.get(url_sum)
    assert resp_sum.status_code == 200
    assert resp_sum.data["data_domains"]["total"] >= 33
    assert resp_sum.data["units_of_measure"]["total"] >= 30
    assert resp_sum.data["frequencies"]["total"] >= 12
