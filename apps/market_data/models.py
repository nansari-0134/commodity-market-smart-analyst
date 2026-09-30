"""
Market Data & Time-Series Observation Models.

Implements the central quantitative storage and ingestion layer of the platform:
- MarketPriceObservation: OHLCV, settlements, volume, and open interest
- FundamentalObservation: Government balances, inventories (EIA, USDA), flows
- CommitmentOfTradersObservation: Disaggregated CFTC positioning (Managed Money, Commercials)

Architectural Directives Enforced:
- Section 7 / Rule 2: Point-in-Time Correctness (observation_date, publication_time, availability_time)
- Section 9 / Rule 5: Native SQL NULL for unobserved metrics (1-bit bitmap efficiency, SIMD vectorization)
"""

from decimal import Decimal
from django.db import models
from apps.core.models import UUIDModel, PointInTimeModel, TimeStampedModel, DataQualityStatus


class MarketPriceObservation(UUIDModel, PointInTimeModel, TimeStampedModel):
    """
    Historical and intraday exchange price bar observations for commodities.
    Supports continuous prompt (front-month) series as well as individual contract expiries.
    """
    commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.CASCADE,
        related_name="price_observations",
        help_text="Canonical underlying physical commodity",
    )
    contract = models.ForeignKey(
        "contracts.ContractSpecification",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="price_observations",
        help_text="Specific derivative contract specification (optional)",
    )
    delivery_month = models.CharField(
        max_length=16,
        blank=True,
        default="",
        db_index=True,
        help_text="Delivery contract month (e.g. '2026-11' or 'CLX26')",
    )
    is_prompt = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flag indicating active benchmark prompt (front-month) contract",
    )
    observation_date = models.DateField(
        db_index=True,
        help_text="Market trading / pricing date",
    )
    open_price = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Session opening price (NULL if unobserved)",
    )
    high_price = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Session high price (NULL if unobserved)",
    )
    low_price = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Session low price (NULL if unobserved)",
    )
    close_price = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Session close price (NULL if unobserved)",
    )
    settlement_price = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        db_index=True,
        help_text="Official exchange daily settlement price (NULL if unobserved)",
    )
    volume = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total contracts traded during session (NULL if unobserved)",
    )
    open_interest = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total active open contracts at session close (NULL if unobserved)",
    )
    quality_status = models.CharField(
        max_length=16,
        choices=DataQualityStatus.choices,
        default=DataQualityStatus.VALID,
        db_index=True,
        help_text="Data quality flag (VALID, MISSING, STALE, SUSPECT, etc.)",
    )
    source_endpoint = models.ForeignKey(
        "endpoints.EndpointMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="price_observations",
        help_text="Endpoint source through which this observation was ingested",
    )
    is_preliminary = models.BooleanField(
        default=False,
        help_text="Preliminary price flag prior to official settlement",
    )
    revision_number = models.PositiveIntegerField(
        default=0,
        help_text="Revision sequence number (0 = initial publication)",
    )

    class Meta:
        ordering = ["-observation_date", "commodity", "delivery_month"]
        indexes = [
            models.Index(fields=["commodity", "observation_date"]),
            models.Index(fields=["commodity", "is_prompt", "observation_date"]),
            models.Index(fields=["observation_date", "is_prompt"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["commodity", "delivery_month", "observation_date", "revision_number"],
                name="unique_market_price_obs",
            )
        ]

    def __str__(self) -> str:
        label = self.delivery_month if self.delivery_month else ("PROMPT" if self.is_prompt else "BAR")
        price = self.settlement_price or self.close_price or "N/A"
        return f"{self.commodity.code} ({label}) @ {self.observation_date}: {price}"

    @property
    def price(self) -> Decimal | None:
        """Preferred price metric: settlement_price, falling back to close_price."""
        return self.settlement_price if self.settlement_price is not None else self.close_price

    @property
    def is_available(self) -> bool:
        """True if an observed settlement or close price is present."""
        return self.price is not None

    @property
    def display_settlement(self) -> str:
        """Presentation string representation honoring Rule 5."""
        return f"{self.price:f}" if self.price is not None else "NOT_AVAILABLE"


class FundamentalObservation(UUIDModel, PointInTimeModel, TimeStampedModel):
    """
    Standardized physical and macroeconomic fundamental observations
    (e.g., EIA Weekly Crude Inventories, Cushing Storage, USDA Ending Stocks).
    """
    variable = models.ForeignKey(
        "variables.VariableMaster",
        on_delete=models.CASCADE,
        related_name="observations",
        help_text="Standardized economic or supply/demand metric",
    )
    observation_date = models.DateField(
        db_index=True,
        help_text="Reference survey/effective date of the metric",
    )
    value = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Observed numerical value. Native SQL NULL represents NOT_AVAILABLE.",
    )
    unit = models.ForeignKey(
        "metadata.UnitMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fundamental_observations",
        help_text="Unit of measure for the observation",
    )
    period_start = models.DateField(
        null=True,
        blank=True,
        help_text="Start date of the measurement survey window",
    )
    period_end = models.DateField(
        null=True,
        blank=True,
        help_text="End date of the measurement survey window (e.g. Friday for EIA)",
    )
    quality_status = models.CharField(
        max_length=16,
        choices=DataQualityStatus.choices,
        default=DataQualityStatus.VALID,
        db_index=True,
        help_text="Data quality flag",
    )
    source_endpoint = models.ForeignKey(
        "endpoints.EndpointMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fundamental_observations",
        help_text="Originating ingestion endpoint",
    )
    is_preliminary = models.BooleanField(
        default=False,
        help_text="Preliminary estimate prior to final official revision",
    )
    revision_number = models.PositiveIntegerField(
        default=0,
        help_text="Revision sequence number (0 = initial release)",
    )

    class Meta:
        ordering = ["-observation_date", "variable"]
        indexes = [
            models.Index(fields=["variable", "observation_date"]),
            models.Index(fields=["observation_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["variable", "observation_date", "revision_number"],
                name="unique_fundamental_obs",
            )
        ]

    def __str__(self) -> str:
        return f"{self.variable.code} @ {self.observation_date}: {self.display_value}"

    @property
    def is_available(self) -> bool:
        """True if an observed numerical value exists and is not null."""
        return self.value is not None

    @property
    def display_value(self) -> str:
        """Presentation string representation honoring Rule 5."""
        if self.value is None:
            return "NOT_AVAILABLE"
        unit_code = f" {self.unit.code}" if self.unit else ""
        return f"{self.value:g}{unit_code}"


class COTReportType(models.TextChoices):
    DISAGGREGATED = "DISAGGREGATED", "Disaggregated (Commodities)"
    LEGACY = "LEGACY", "Legacy COT (Commercial vs Non-Commercial)"
    FINANCIAL = "FINANCIAL", "Traders in Financial Futures (TFF)"


class CommitmentOfTradersObservation(UUIDModel, PointInTimeModel, TimeStampedModel):
    """
    CFTC Commitment of Traders (COT) positional data.
    Tracks institutional positioning across Commercial Hedgers, Managed Money, and Non-Reportables.
    Survey date is Tuesday; official publication is Friday afternoon.
    """
    commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.CASCADE,
        related_name="cot_observations",
        help_text="Underlying physical commodity",
    )
    observation_date = models.DateField(
        db_index=True,
        help_text="CFTC survey Tuesday cutoff date",
    )
    report_type = models.CharField(
        max_length=20,
        choices=COTReportType.choices,
        default=COTReportType.DISAGGREGATED,
        db_index=True,
        help_text="COT report classification",
    )
    open_interest = models.BigIntegerField(
        help_text="Total reportable open interest",
    )
    prod_merc_long = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Producer/Merchant/Processor/User Long contracts",
    )
    prod_merc_short = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Producer/Merchant/Processor/User Short contracts",
    )
    swap_long = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Swap Dealers Long contracts",
    )
    swap_short = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Swap Dealers Short contracts",
    )
    swap_spread = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Swap Dealers Spreading contracts",
    )
    money_manager_long = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Managed Money (Hedge Funds / CTAs) Long contracts",
    )
    money_manager_short = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Managed Money (Hedge Funds / CTAs) Short contracts",
    )
    money_manager_spread = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Managed Money Spreading contracts",
    )
    other_rept_long = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Other Reportables Long contracts",
    )
    other_rept_short = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Other Reportables Short contracts",
    )
    non_rept_long = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Non-Reportable (Small Retail Traders) Long contracts",
    )
    non_rept_short = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Non-Reportable (Small Retail Traders) Short contracts",
    )
    quality_status = models.CharField(
        max_length=16,
        choices=DataQualityStatus.choices,
        default=DataQualityStatus.VALID,
        db_index=True,
        help_text="Data quality flag",
    )
    source_endpoint = models.ForeignKey(
        "endpoints.EndpointMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cot_observations",
        help_text="Originating ingestion endpoint",
    )

    class Meta:
        ordering = ["-observation_date", "commodity"]
        indexes = [
            models.Index(fields=["commodity", "observation_date"]),
            models.Index(fields=["observation_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["commodity", "observation_date", "report_type"],
                name="unique_cot_obs",
            )
        ]

    def __str__(self) -> str:
        return (
            f"COT {self.commodity.code} ({self.report_type}) @ {self.observation_date}: "
            f"MM Net {self.money_manager_net:+d}"
        )

    @property
    def money_manager_net(self) -> int:
        """Net speculative fund positioning: Long minus Short."""
        longs = self.money_manager_long or 0
        shorts = self.money_manager_short or 0
        return longs - shorts

    @property
    def commercial_net(self) -> int:
        """Net physical commercial hedging positioning: (Prod/Merc + Swap Long) - (Prod/Merc + Swap Short)."""
        longs = (self.prod_merc_long or 0) + (self.swap_long or 0)
        shorts = (self.prod_merc_short or 0) + (self.swap_short or 0)
        return longs - shorts

    @property
    def money_manager_net_pct_oi(self) -> float:
        """Net Managed Money positioning as a percentage of Total Open Interest."""
        if not self.open_interest:
            return 0.0
        return round((self.money_manager_net / self.open_interest) * 100, 2)

    @property
    def commercial_net_pct_oi(self) -> float:
        """Net Commercial hedging positioning as a percentage of Total Open Interest."""
        if not self.open_interest:
            return 0.0
        return round((self.commercial_net / self.open_interest) * 100, 2)


class EventType(models.TextChoices):
    """Categorical classification of material commodity catalyst events."""
    INVENTORY_RELEASE = "INVENTORY_RELEASE", "Inventory & Storage Release"
    CROP_REPORT = "CROP_REPORT", "Crop & Agricultural Balance Report"
    POLICY_DECISION = "POLICY_DECISION", "Policy / Quota / Central Bank Decision"
    OUTAGE_INCIDENT = "OUTAGE_INCIDENT", "Refinery / Pipeline / Port Outage"
    WEATHER_ANOMALY = "WEATHER_ANOMALY", "Weather / Freeze / Drought Anomaly"
    GEOPOLITICAL = "GEOPOLITICAL", "Geopolitical / Sanction / Shipping Escalation"


class MarketEvent(UUIDModel, PointInTimeModel, TimeStampedModel):
    """
    Timestamped material market catalyst event for Event Study analysis.
    Stores scheduled vs actual release times, consensus expectations, and measured surprises.
    """
    event_type = models.CharField(
        max_length=32,
        choices=EventType.choices,
        default=EventType.INVENTORY_RELEASE,
        db_index=True,
        help_text="Classification of market catalyst event",
    )
    name = models.CharField(
        max_length=255,
        help_text="Canonical event name (e.g. 'EIA WPSR Cushing Crude Stocks')",
    )
    commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        help_text="Primary affected commodity (optional for macro events)",
    )
    dataset = models.ForeignKey(
        "datasets.DatasetMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        help_text="Associated benchmark dataset from catalog",
    )
    source = models.ForeignKey(
        "providers.ProviderMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        help_text="Originating data vendor / government agency",
    )
    scheduled_time = models.DateTimeField(
        db_index=True,
        help_text="Official scheduled UTC release timestamp",
    )
    actual_value = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Reported actual observation metric (NULL if unobserved)",
    )
    expected_value = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Market consensus / survey forecast (NULL if unobserved)",
    )
    prior_value = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Previous period observation value",
    )
    surprise = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Measured surprise: actual minus expected (NULL if unobserved)",
    )
    standardized_surprise = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Standardized surprise (z-score against historical consensus errors)",
    )
    unit = models.ForeignKey(
        "metadata.UnitMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Unit of measure for reported values",
    )
    data_quality = models.CharField(
        max_length=16,
        choices=DataQualityStatus.choices,
        default=DataQualityStatus.VALID,
        help_text="Data quality audit flag",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Qualitative commentary, revised release notes, or analyst remarks",
    )

    class Meta:
        ordering = ["-scheduled_time", "event_type"]
        indexes = [
            models.Index(fields=["event_type", "scheduled_time"]),
            models.Index(fields=["commodity", "scheduled_time"]),
        ]

    def __str__(self) -> str:
        actual_str = f"{self.actual_value:.2f}" if self.actual_value is not None else "PENDING"
        return f"{self.name} @ {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}: {actual_str}"

    @property
    def computed_surprise(self) -> float | None:
        """Calculate actual - expected dynamically if not stored."""
        if self.actual_value is not None and self.expected_value is not None:
            return float(self.actual_value - self.expected_value)
        return float(self.surprise) if self.surprise is not None else None


class OptionsObservation(UUIDModel, PointInTimeModel, TimeStampedModel):
    """
    Daily options-implied volatility surface and positioning metrics.
    Enforces Rule 5 native SQL NULL for unobserved metrics.
    """
    commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.CASCADE,
        related_name="options_observations",
        help_text="Canonical underlying physical commodity",
    )
    contract = models.ForeignKey(
        "contracts.ContractSpecification",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="options_observations",
        help_text="Derivative contract specification (optional)",
    )
    delivery_month = models.CharField(
        max_length=16,
        blank=True,
        default="M1",
        db_index=True,
        help_text="Delivery contract month or tenor (e.g. 'M1', 'M2', ..., 'M24')",
    )
    observation_date = models.DateField(
        db_index=True,
        help_text="Market trading / pricing date",
    )
    atm_implied_volatility = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="At-The-Money (ATM) implied volatility in percent (e.g. 28.50%)",
    )
    realized_volatility_30d = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="30-day historical realized volatility in percent",
    )
    iv_rv_spread = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Volatility risk premium: IV minus 30d Realized Volatility",
    )
    skew_25d = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="25-Delta Risk Reversal skew: 25d Call IV minus 25d Put IV",
    )
    term_structure_slope = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Options term structure slope: Prompt IV minus 3M IV",
    )
    put_call_volume_ratio = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Total Put volume divided by Total Call volume",
    )
    put_call_oi_ratio = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Total Put Open Interest divided by Total Call Open Interest",
    )
    total_options_volume = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total daily options contract volume across all strikes",
    )
    total_options_oi = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Total options Open Interest across all strikes",
    )
    data_quality = models.CharField(
        max_length=16,
        choices=DataQualityStatus.choices,
        default=DataQualityStatus.VALID,
        help_text="Data quality audit flag",
    )
    source_endpoint = models.ForeignKey(
        "endpoints.EndpointMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="options_observations",
        help_text="Originating ingestion endpoint",
    )

    class Meta:
        ordering = ["-observation_date", "commodity", "delivery_month"]
        indexes = [
            models.Index(fields=["commodity", "observation_date"]),
            models.Index(fields=["commodity", "delivery_month", "observation_date"]),
            models.Index(fields=["observation_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["commodity", "observation_date", "contract", "delivery_month"],
                name="unique_options_obs",
            )
        ]

    def __str__(self) -> str:
        iv_str = f"{self.atm_implied_volatility:.1f}%" if self.atm_implied_volatility is not None else "NULL"
        return f"Options {self.commodity.code} ({self.delivery_month or 'M1'}) @ {self.observation_date}: ATM IV {iv_str}"
