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
