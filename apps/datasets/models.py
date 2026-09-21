"""
Dataset Master Models.

Defines canonical dataset catalog records, update cadences, release schedules,
ingestion modes, revision policies, and service level agreements (SLAs).
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel, TimeStampedModel


class DataCategory(models.TextChoices):
    MARKET_PRICES = "MARKET_PRICES", _("Market Prices & Spreads")
    INVENTORIES_STOCKS = "INVENTORIES_STOCKS", _("Inventories & Warehouse Stocks")
    SUPPLY_DEMAND = "SUPPLY_DEMAND", _("Supply & Demand Balances")
    TRADE_FLOWS = "TRADE_FLOWS", _("Trade Flows & Customs")
    POSITIONING = "POSITIONING", _("Trader Positioning & COT")
    WEATHER_CLIMATE = "WEATHER_CLIMATE", _("Weather & Satellite Climate")
    MACROECONOMIC = "MACROECONOMIC", _("Macroeconomic & FX Rates")
    PRODUCTION_CAPACITY = "PRODUCTION_CAPACITY", _("Production & Extraction")
    ENVIRONMENTAL = "ENVIRONMENTAL", _("Environmental & Emissions")


class UpdateCadence(models.TextChoices):
    REALTIME_STREAM = "REALTIME_STREAM", _("Real-Time Tick / Continuous Stream")
    HOURLY = "HOURLY", _("Hourly Snapshots")
    DAILY_EOD = "DAILY_EOD", _("Daily End-of-Day")
    WEEKLY_FIXED_DAY = "WEEKLY_FIXED_DAY", _("Weekly Fixed Day")
    MONTHLY_CALENDAR_DAY = "MONTHLY_CALENDAR_DAY", _("Monthly Specific Date")
    QUARTERLY = "QUARTERLY", _("Quarterly")
    SEASONAL_CROP_CYCLE = "SEASONAL_CROP_CYCLE", _("Seasonal Crop Cycle")
    EVENT_DRIVEN = "EVENT_DRIVEN", _("Event-Driven / Ad-Hoc")


class IngestionMode(models.TextChoices):
    PULL_SCHEDULED_BATCH = "PULL_SCHEDULED_BATCH", _("Scheduled Batch Pull (REST API / FTP)")
    PULL_POLL_CHANGE_DETECTION = "PULL_POLL_CHANGE_DETECTION", _("Polling with Change Detection / ETag")
    PUSH_WEBHOOK_STREAM = "PUSH_WEBHOOK_STREAM", _("Inbound Webhook Stream")
    PUSH_MESSAGE_QUEUE = "PUSH_MESSAGE_QUEUE", _("Message Queue (Kafka / RabbitMQ)")
    MANUAL_INGESTION = "MANUAL_INGESTION", _("Manual Analyst Upload")


class RetentionPolicy(models.TextChoices):
    INDEFINITE_POINT_IN_TIME = "INDEFINITE_POINT_IN_TIME", _("Indefinite with Point-in-Time History")
    ROLLING_10_YEARS = "ROLLING_10_YEARS", _("Rolling 10 Years")
    ROLLING_5_YEARS = "ROLLING_5_YEARS", _("Rolling 5 Years")
    INTRADAY_90_DAYS = "INTRADAY_90_DAYS", _("High-Frequency 90 Days")


class LicenseType(models.TextChoices):
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN", _("Public Domain / Open Data")
    PROPRIETARY_COMMERCIAL = "PROPRIETARY_COMMERCIAL", _("Proprietary Commercial Vendor")
    EXCHANGE_LICENSED = "EXCHANGE_LICENSED", _("Exchange Licensed Market Data")
    INTERNAL_DERIVED = "INTERNAL_DERIVED", _("Internal Derived / Quantitative Model")


class DatasetMaster(UUIDModel, TimeStampedModel):
    """
    Canonical dataset registry representing a structured, observable series collection
    published by an external authority, market venue, or internal calculation engine.
    """

    code = models.CharField(
        max_length=60,
        unique=True,
        db_index=True,
        help_text="Canonical unique identifier (e.g. CME_FUTURES_EOD, EIA_WPSR_PETROLEUM, USDA_WASDE).",
    )
    name = models.CharField(
        max_length=150,
        help_text="Descriptive title of the dataset series.",
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed methodology, scope, and coverage description.",
    )
    domain = models.ForeignKey(
        "metadata.DataDomainMaster",
        on_delete=models.PROTECT,
        related_name="datasets",
        help_text="Parent data domain taxonomy classification.",
    )
    primary_commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_datasets",
        help_text="Primary benchmark commodity anchor (if single-asset focused).",
    )
    commodities = models.ManyToManyField(
        "commodities.CommodityMaster",
        blank=True,
        related_name="datasets",
        help_text="All physical commodities covered by this dataset (multi-asset flexibility).",
    )
    exchange = models.ForeignKey(
        "exchanges.ExchangeMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="datasets",
        help_text="Associated exchange venue (if venue-specific).",
    )
    frequency = models.ForeignKey(
        "metadata.FrequencyMaster",
        on_delete=models.PROTECT,
        related_name="datasets",
        help_text="Standard temporal observation frequency.",
    )
    data_category = models.CharField(
        max_length=40,
        choices=DataCategory.choices,
        default=DataCategory.MARKET_PRICES,
        help_text="Functional data categorization.",
    )
    update_cadence = models.CharField(
        max_length=40,
        choices=UpdateCadence.choices,
        default=UpdateCadence.DAILY_EOD,
        help_text="Publication timing frequency.",
    )
    ingestion_mode = models.CharField(
        max_length=40,
        choices=IngestionMode.choices,
        default=IngestionMode.PULL_SCHEDULED_BATCH,
        help_text="Protocol used by ETL pipelines to acquire data.",
    )
    release_schedule = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured release timing details (e.g. day_of_week, time_local, timezone).",
    )
    retention_policy = models.CharField(
        max_length=40,
        choices=RetentionPolicy.choices,
        default=RetentionPolicy.INDEFINITE_POINT_IN_TIME,
        help_text="Historical data retention rule.",
    )
    license_type = models.CharField(
        max_length=40,
        choices=LicenseType.choices,
        default=LicenseType.PUBLIC_DOMAIN,
        help_text="Commercial or regulatory usage rights.",
    )
    point_in_time_enabled = models.BooleanField(
        default=True,
        help_text="Whether PointInTimeModel observation timestamps and revision tracking are enforced.",
    )
    supports_revisions = models.BooleanField(
        default=True,
        help_text="Whether reporting authority issues retroactive revisions to historical figures.",
    )
    sla_max_delay_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Maximum tolerable delay between scheduled release and completed ingestion before alert.",
    )
    source_authority = models.CharField(
        max_length=150,
        help_text="Authoritative publishing agency or organization (e.g. USDA, EIA, CFTC, CME Group).",
    )
    documentation_url = models.URLField(
        blank=True,
        help_text="Link to official methodology or agency data dictionary.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this dataset is actively monitored and ingested.",
    )
    display_order = models.PositiveIntegerField(
        default=100,
        help_text="Sorting order in dashboards and catalog indexes.",
    )

    class Meta:
        db_table = "datasets_master"
        ordering = ["display_order", "code"]
        verbose_name = _("Dataset Master")
        verbose_name_plural = _("Dataset Master Catalog")

    def __str__(self) -> str:
        return f"{self.code}: {self.name} ({self.source_authority})"
