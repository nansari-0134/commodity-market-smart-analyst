"""
Commodity Master, Deliverable Grade Chemistry, and Multi-Exchange Listings.

Implements architectural specifications from:
- Section 10 (Major Metadata Entities: commodity_master)
- Section 11 (Commodity Hierarchy: Exchange -> Commodity -> Product -> Instrument -> Contract)
- Phase 4: Canonical Physical Commodity Master, Deliverable Grades, and Multi-Venue Listings.
"""
from decimal import Decimal
from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel


class CommoditySector(models.TextChoices):
    """High-level commodity classification sectors."""
    ENERGY = "ENERGY", "Energy (Crude, Gas, Power, Refined)"
    AGRICULTURE = "AGRICULTURE", "Agriculture (Grains, Oilseeds, Softs)"
    LIVESTOCK = "LIVESTOCK", "Livestock & Dairy"
    METALS_BASE = "METALS_BASE", "Industrial / Base Metals"
    METALS_PRECIOUS = "METALS_PRECIOUS", "Precious Metals"
    FREIGHT_BULK = "FREIGHT_BULK", "Bulk Freight & Shipping"
    ENVIRONMENTAL = "ENVIRONMENTAL", "Environmental & Carbon Allowances"


class SettlementMethod(models.TextChoices):
    """Contract settlement mechanism: Physical delivery vs. Cash index settlement."""
    PHYSICAL = "PHYSICAL", "Physical Delivery"
    CASH = "CASH", "Cash Settlement"


class LiquidityTier(models.TextChoices):
    """Exchange listing liquidity & open interest tier."""
    BENCHMARK = "BENCHMARK", "Global Benchmark Volume"
    HIGH = "HIGH", "High Institutional Volume & Open Interest"
    ACTIVE = "ACTIVE", "Active Liquid Regional Contract"


class CommodityMaster(UUIDModel, TimeStampedModel):
    """
    Canonical reference model for a physical commodity.
    Represents the underlying physical good across global derivative venues.
    """
    code = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Canonical internal symbol (e.g. 'CL', 'BRENT', 'NG', 'CORN', 'GOLD')",
    )
    name = models.CharField(
        max_length=128,
        help_text="Human-readable title (e.g. 'Light Sweet Crude Oil (WTI)', 'Henry Hub Natural Gas')",
    )
    sector = models.CharField(
        max_length=32,
        choices=CommoditySector.choices,
        db_index=True,
        help_text="High-level commodity sector classification",
    )
    group = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Industry grouping (e.g. 'CRUDE_OIL', 'REFINED_PRODUCTS', 'GRAINS', 'SOFTS', 'PRECIOUS_METALS')",
    )
    primary_exchange = models.ForeignKey(
        "exchanges.ExchangeMaster",
        on_delete=models.PROTECT,
        related_name="benchmark_commodities",
        help_text="Global pricing benchmark venue (e.g. NYMEX for WTI, ICE_EU for Brent, COMEX for Gold)",
    )
    base_unit = models.ForeignKey(
        "metadata.UnitMaster",
        on_delete=models.PROTECT,
        related_name="base_commodities",
        help_text="Base physical unit of measure (e.g. BBL, MMBTU, BU, MT, TOZ, LBS)",
    )
    pricing_unit = models.ForeignKey(
        "metadata.UnitMaster",
        on_delete=models.PROTECT,
        related_name="pricing_commodities",
        help_text="Default price quote unit (e.g. USD_BBL, USD_MMBTU, USC_BU, USD_TOZ, USD_MT)",
    )
    standard_lot_size = models.DecimalField(
        max_digits=16,
        decimal_places=4,
        default=Decimal("1.0"),
        help_text="Standard contract physical lot size in benchmark units (e.g. 1000 bbl, 5000 bu, 100 toz)",
    )
    standard_lot_unit = models.ForeignKey(
        "metadata.UnitMaster",
        on_delete=models.PROTECT,
        related_name="lot_commodities",
        help_text="Physical unit for contract lot size",
    )
    minimum_tick_size = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal("0.01"),
        help_text="Minimum allowable price fluctuation (e.g. 0.01 for WTI, 0.001 for NG, 0.0025 for Corn)",
    )
    tick_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=Decimal("10.00"),
        help_text="Monetary value of one minimum price fluctuation per contract (e.g. $10.00 for WTI, $12.50 for Corn)",
    )
    tick_currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Currency ISO code of tick value (e.g. USD, EUR, MYR, INR)",
    )
    settlement_method = models.CharField(
        max_length=16,
        choices=SettlementMethod.choices,
        default=SettlementMethod.PHYSICAL,
        help_text="Default settlement mechanism of benchmark contract",
    )
    hs_code = models.CharField(
        max_length=16,
        blank=True,
        default="",
        help_text="Harmonized System 6-digit tariff code (e.g. 2709.00 for crude oil, 1005.90 for corn)",
    )
    deliverable_grade_standard = models.CharField(
        max_length=256,
        blank=True,
        default="",
        help_text="Primary deliverable grade specification (e.g. 'U.S. No. 2 Yellow Corn', 'API 37-42°, Sulfur <= 0.42%')",
    )
    quality_specifications = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured physical/chemical parameters: API gravity, sulfur, moisture, purity, test weight, etc.",
    )
    primary_delivery_hub = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="Benchmark pricing point / physical delivery terminal (e.g. 'Cushing, Oklahoma', 'Henry Hub, Louisiana')",
    )
    delivery_hub_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Hub geography, coordinates, storage terminals, and pipeline interconnects",
    )
    crop_year_start_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Calendar month (1-12) marking crop marketing year start (e.g. 9 for Sept US Corn/Soybeans)",
    )
    peak_production_months = models.JSONField(
        default=list,
        blank=True,
        help_text="List of calendar months with peak harvest or production output",
    )
    peak_demand_months = models.JSONField(
        default=list,
        blank=True,
        help_text="List of calendar months with peak seasonal consumption",
    )
    seasonality_notes = models.TextField(
        blank=True,
        default="",
        help_text="Institutional commentary on seasonal supply, demand, and basis tendencies",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Comprehensive commercial scope and market profile",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Flag indicating if commodity is actively tracked by analytics",
    )
    display_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="UI and reporting ordering rank",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata, conversion ratios, and external identifiers",
    )

    class Meta:
        verbose_name = "Commodity Master"
        verbose_name_plural = "Commodities Master"
        ordering = ["sector", "display_order", "code"]
        indexes = [
            models.Index(fields=["sector", "is_active"]),
            models.Index(fields=["group", "is_active"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def exchange_count(self) -> int:
        """Returns total active exchange listings."""
        return self.exchange_listings.filter(is_active=True).count()


class CommodityExchangeListing(UUIDModel, TimeStampedModel):
    """
    Represents the same physical commodity trading on multiple liquid exchanges.
    Filters out dormant/zombie contracts and captures venue-specific liquidity (Volume & Open Interest).
    """
    commodity = models.ForeignKey(
        CommodityMaster,
        on_delete=models.CASCADE,
        related_name="exchange_listings",
        help_text="The underlying physical commodity",
    )
    exchange = models.ForeignKey(
        "exchanges.ExchangeMaster",
        on_delete=models.PROTECT,
        related_name="commodity_listings",
        help_text="The trading venue where this contract executes",
    )
    ticker_symbol = models.CharField(
        max_length=32,
        db_index=True,
        help_text="Exchange-specific ticker symbol (e.g. 'CL' on NYMEX, 'CRUDEOIL' on MCX, 'GC' on COMEX)",
    )
    contract_size = models.DecimalField(
        max_digits=16,
        decimal_places=4,
        help_text="Contract lot size on this specific venue",
    )
    contract_unit = models.ForeignKey(
        "metadata.UnitMaster",
        on_delete=models.PROTECT,
        related_name="listing_units",
        help_text="Unit of measure for this venue's contract lot",
    )
    settlement_method = models.CharField(
        max_length=16,
        choices=SettlementMethod.choices,
        default=SettlementMethod.PHYSICAL,
        help_text="Settlement mechanism on this specific exchange (e.g. MCX Crude is Cash, NYMEX is Physical)",
    )
    is_primary_benchmark = models.BooleanField(
        default=False,
        help_text="Flag indicating if this venue is the global reference pricing contract",
    )
    liquidity_tier = models.CharField(
        max_length=32,
        choices=LiquidityTier.choices,
        default=LiquidityTier.ACTIVE,
        help_text="Market liquidity and open interest tier",
    )
    typical_daily_volume = models.PositiveIntegerField(
        default=0,
        help_text="Typical average daily contract volume (ADV)",
    )
    typical_open_interest = models.PositiveIntegerField(
        default=0,
        help_text="Typical active open interest (OI) in contracts",
    )
    trading_currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Trading quotation currency (e.g. USD, INR, CNY, EUR, MYR)",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this listing is actively monitored",
    )

    class Meta:
        verbose_name = "Commodity Exchange Listing"
        verbose_name_plural = "Commodity Exchange Listings"
        ordering = ["commodity", "-is_primary_benchmark", "-typical_daily_volume"]
        unique_together = [("commodity", "exchange")]
        indexes = [
            models.Index(fields=["exchange", "ticker_symbol"]),
            models.Index(fields=["commodity", "is_primary_benchmark"]),
        ]

    def __str__(self):
        return f"{self.commodity.code} on {self.exchange.code} ({self.ticker_symbol})"
