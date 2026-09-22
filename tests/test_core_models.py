"""
Tests for core abstract models, PointInTimeModel, and DataQualityStatus enums.
"""
import uuid
import pytest
from django.db import models
from django.utils import timezone
from apps.core.models import (
    UUIDModel,
    TimeStampedModel,
    PointInTimeModel,
    AuditModel,
    DataQualityStatus,
)


def test_data_quality_status_choices():
    """Verify Section 9 data quality statuses are accurately represented."""
    expected = {"VALID", "WARNING", "INVALID", "MISSING", "STALE", "DUPLICATE", "SUSPECT"}
    actual = {choice.value for choice in DataQualityStatus}
    assert expected == actual


def test_abstract_models_field_definitions():
    """Verify field definitions on abstract base models."""
    # PointInTimeModel fields
    pit_fields = {f.name for f in PointInTimeModel._meta.fields}
    expected_pit = {
        "event_time",
        "observation_time",
        "effective_time",
        "publication_time",
        "availability_time",
        "ingestion_time",
    }
    assert expected_pit.issubset(pit_fields)

    # TimeStampedModel fields
    ts_fields = {f.name for f in TimeStampedModel._meta.fields}
    assert {"created_at", "updated_at"}.issubset(ts_fields)

    # UUIDModel fields
    uuid_fields = {f.name for f in UUIDModel._meta.fields}
    assert "id" in uuid_fields
    id_field = UUIDModel._meta.get_field("id")
    assert isinstance(id_field, models.UUIDField)
    assert id_field.primary_key is True

    # AuditModel fields
    audit_fields = {f.name for f in AuditModel._meta.fields}
    assert {"is_active", "notes", "created_at", "updated_at"}.issubset(audit_fields)


def test_abstract_observation_null_handling():
    """Verify AbstractObservation adheres to the null-as-NOT_AVAILABLE high-performance standard."""
    from apps.core.models import AbstractObservation

    obs_fields = {f.name for f in AbstractObservation._meta.fields}
    assert {"id", "value", "quality_status", "event_time", "observation_time", "availability_time"}.issubset(obs_fields)

    value_field = AbstractObservation._meta.get_field("value")
    assert value_field.null is True
    assert value_field.blank is True

    # Test dynamic property behaviors on an uncommitted dummy instance
    class ConcreteObservation(AbstractObservation):
        class Meta:
            app_label = "core"

    # 1. Null / missing value
    null_obs = ConcreteObservation(value=None)
    assert null_obs.is_available is False
    assert null_obs.display_value == "NOT_AVAILABLE"

    # 2. Legitimate zero value
    zero_obs = ConcreteObservation(value=0.0)
    assert zero_obs.is_available is True
    assert zero_obs.display_value == "0"

    # 3. Positive numeric value
    pos_obs = ConcreteObservation(value=78.50)
    assert pos_obs.is_available is True
    assert pos_obs.display_value == "78.5"

