"""
Core abstract models, enums, and base utilities for the platform.

Implements architectural requirements:
- Point-in-time correctness (Section 7)
- Data quality statuses (Section 9)
- Auditing and timestamps (Section 43)
"""
import uuid
from django.db import models
from django.utils import timezone


class DataQualityStatus(models.TextChoices):
    """Explicit data quality classification states as per Section 9."""
    VALID = "VALID", "Valid"
    WARNING = "WARNING", "Warning"
    INVALID = "INVALID", "Invalid"
    MISSING = "MISSING", "Missing"
    STALE = "STALE", "Stale"
    DUPLICATE = "DUPLICATE", "Duplicate"
    SUSPECT = "SUSPECT", "Suspect"


class UUIDModel(models.Model):
    """Abstract model providing a standard UUID primary key."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Universally unique identifier",
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """
    Abstract model tracking creation and last modification timestamps.
    Indexed for audit queries.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when the database record was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        help_text="Timestamp when the database record was last modified",
    )

    class Meta:
        abstract = True


class PointInTimeModel(models.Model):
    """
    Abstract model strictly enforcing point-in-time correctness (Section 7).

    Historical research and backtests MUST use only information available
    to the market at that exact point in time to prevent look-ahead bias.
    """
    event_time = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Time when the real-world event occurred",
    )
    observation_time = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Time when the metric/observation was recorded",
    )
    effective_time = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Time when the data becomes active or in effect",
    )
    publication_time = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Time when the provider/source published the data",
    )
    availability_time = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Exact point-in-time when data was accessible to the market (anti-lookahead timestamp)",
    )
    ingestion_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="System ingestion timestamp",
    )

    class Meta:
        abstract = True


class AuditModel(TimeStampedModel):
    """
    Abstract model adding standard soft-delete and administrative notes.
    """
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indicates whether this record is active",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Administrative notes or provenance context",
    )

    class Meta:
        abstract = True
