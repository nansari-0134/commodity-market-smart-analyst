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
