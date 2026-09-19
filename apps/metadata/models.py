"""
Metadata Catalog, Data Domains, Units of Measure, and Observation Frequencies.

Implements architectural specifications from:
- Section 10 (Major Metadata Entities: data_domain_master)
- Section 12 (Data Domains: 33 Canonical commodity & market domains)
- Section 3 & 43 (Data Contracts, Units of Measure, and Frequency standards)
"""
from decimal import Decimal
from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel


class DataDomainCategory(models.TextChoices):
    """Broad categorization for data domains."""
    MARKET = "MARKET", "Financial & Exchange Market"
    PHYSICAL = "PHYSICAL", "Physical & Supply Chain"
    MACRO = "MACRO", "Macroeconomic & Policy"
    WEATHER = "WEATHER", "Weather & Climate"
    QUALITATIVE = "QUALITATIVE", "News, Events & Documents"
    DERIVED = "DERIVED", "Quant, Narratives & Strategy"


class DataDomainMaster(UUIDModel, TimeStampedModel):
    """
    Hierarchical master taxonomy for canonical data domains (Section 12).
    Every dataset and variable in the system maps to one of these domains.
    """
    code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Machine-readable canonical identifier (e.g. 'FUTURES_CURVES', 'INVENTORIES')",
    )
    name = models.CharField(
        max_length=128,
        help_text="Human-readable title for the domain",
    )
    category = models.CharField(
        max_length=32,
        choices=DataDomainCategory.choices,
        default=DataDomainCategory.MARKET,
        db_index=True,
        help_text="High-level category grouping",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subdomains",
        help_text="Parent domain if part of a sub-domain hierarchy (e.g. Fundamentals -> Inventory)",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Scope, definitions, and domain boundaries",
    )
    display_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Sorting order in user interfaces and reports",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Flag indicating if this domain is active in the platform",
    )

    class Meta:
        verbose_name = "Data Domain"
        verbose_name_plural = "Data Domains"
        ordering = ["category", "display_order", "name"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    @property
    def hierarchy_path(self) -> str:
        """Returns the full hierarchical string path for this domain."""
        if self.parent:
            return f"{self.parent.hierarchy_path} > {self.name}"
        return self.name


class UnitType(models.TextChoices):
    """Classification of unit dimensions."""
    VOLUME = "VOLUME", "Volume"
    MASS = "MASS", "Mass / Weight"
    ENERGY = "ENERGY", "Energy"
    CURRENCY = "CURRENCY", "Currency"
    PRICE_PER_UNIT = "PRICE_PER_UNIT", "Price per Unit"
    RATIO = "RATIO", "Ratio / Spread / Percentage"
    INDEX = "INDEX", "Index Points"
    COUNT = "COUNT", "Count / Head / Vessel"
    TEMPERATURE = "TEMPERATURE", "Temperature / Degree Days"


class UnitMaster(UUIDModel, TimeStampedModel):
    """
    Standardized measurement units for physical and financial observations.
    Ensures deterministic arithmetic in the quantitative and balance engines.
    """
    code = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Canonical unit code (e.g. 'BBL', 'MT', 'BU', 'MMBTU', 'USD_BBL')",
    )
    name = models.CharField(
        max_length=128,
        help_text="Full name (e.g. 'Barrels', 'Metric Tons', 'Bushels')",
    )
    symbol = models.CharField(
        max_length=16,
        blank=True,
        default="",
        help_text="Abbreviated symbol or display glyph (e.g. 'bbl', 't', 'bu', '$')",
    )
    unit_type = models.CharField(
        max_length=32,
        choices=UnitType.choices,
        db_index=True,
        help_text="Dimensional type of unit",
    )
    base_unit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="derived_units",
        help_text="Reference base unit for standard mathematical conversion",
    )
    conversion_factor = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal("1.0"),
        help_text="Multiplier to convert this unit into its base_unit (value * factor = base_value)",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Contextual notes on unit specifications or regional conventions",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Flag indicating if this unit is active",
    )

    class Meta:
        verbose_name = "Unit of Measure"
        verbose_name_plural = "Units of Measure"
        ordering = ["unit_type", "code"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def to_base_unit(self, value: Decimal | float | int) -> Decimal:
        """Converts a value expressed in this unit to the base unit."""
        dec_val = Decimal(str(value))
        if not self.base_unit or self.base_unit_id == self.id:
            return dec_val
        return dec_val * self.conversion_factor

    def convert_to(self, value: Decimal | float | int, target_unit: "UnitMaster") -> Decimal:
        """
        Converts a value from this unit to another target unit.
        Both units must share the same dimension/base unit.
        """
        if self.unit_type != target_unit.unit_type:
            raise ValueError(
                f"Cannot convert between incompatible unit types: '{self.unit_type}' and '{target_unit.unit_type}'"
            )
        self_base_id = self.base_unit_id or self.id
        target_base_id = target_unit.base_unit_id or target_unit.id
        if self_base_id != target_base_id:
            raise ValueError(
                f"Units '{self.code}' and '{target_unit.code}' do not share a common base unit for conversion"
            )
        base_val = self.to_base_unit(value)
        if not target_unit.base_unit or target_unit.base_unit_id == target_unit.id or target_unit.conversion_factor == 0:
            return base_val
        return base_val / target_unit.conversion_factor


class FrequencyMaster(UUIDModel, TimeStampedModel):
    """
    Standard observation and publication frequencies for datasets and time series.
    Used by the ingestion scheduler and data quality monitors for staleness checks.
    """
    code = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Standard frequency code (e.g. 'TICK', '1M', 'DAILY', 'WEEKLY', 'EVENT_DRIVEN')",
    )
    name = models.CharField(
        max_length=128,
        help_text="Human-readable frequency name",
    )
    standard_interval_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Nominal interval duration in seconds (null for irregular/event-driven)",
    )
    is_regular = models.BooleanField(
        default=True,
        help_text="True for scheduled regular intervals; False for ad-hoc or event-driven releases",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Operational cadence details (e.g. 'Released every Wednesday at 10:30 AM EST')",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Flag indicating if this frequency is currently supported",
    )

    class Meta:
        verbose_name = "Observation Frequency"
        verbose_name_plural = "Observation Frequencies"
        ordering = ["standard_interval_seconds", "name"]

    def __str__(self):
        return f"{self.name} [{self.code}]"
