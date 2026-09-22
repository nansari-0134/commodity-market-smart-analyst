"""
Variable Master Models.

Defines canonical standardized metrics, economic series, stock vs. flow aggregation
behaviors, dimensional units, and default display transformations.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import UUIDModel, TimeStampedModel


class VariableDataType(models.TextChoices):
    DECIMAL = "DECIMAL", _("Floating Point / Decimal")
    INTEGER = "INTEGER", _("Integer / Count")
    PERCENTAGE_RATIO = "PERCENTAGE_RATIO", _("Percentage / Ratio (0-100 or 0-1)")
    BOOLEAN = "BOOLEAN", _("Binary Boolean Flag")
    TEXT = "TEXT", _("Categorical / String Label")


class AggregationMethod(models.TextChoices):
    LAST = "LAST", _("Last Observation (Stock / Snapshot / Spot / Inventory)")
    SUM = "SUM", _("Cumulative Sum (Flow / Production / Exports / Volume)")
    AVG = "AVG", _("Arithmetic Mean (Index / Rate / Temperature)")
    MAX = "MAX", _("Peak / Maximum (Capacity / High Price)")
    MIN = "MIN", _("Trough / Minimum (Low Price / Min Level)")


class SeasonalAdjustment(models.TextChoices):
    UNADJUSTED = "UNADJUSTED", _("Raw / Not Seasonally Adjusted (NSA)")
    SEASONALLY_ADJUSTED = "SEASONALLY_ADJUSTED", _("Seasonally Adjusted (SA)")


class DisplayTransformation(models.TextChoices):
    RAW_LEVEL = "RAW_LEVEL", _("Raw Level Value")
    DIFF_1D = "DIFF_1D", _("1-Period Difference")
    DIFF_1W = "DIFF_1W", _("1-Week Difference")
    DIFF_1M = "DIFF_1M", _("1-Month Difference")
    PCT_CHANGE_1D = "PCT_CHANGE_1D", _("1-Day Percent Change")
    PCT_CHANGE_1W = "PCT_CHANGE_1W", _("1-Week Percent Change")
    PCT_CHANGE_1M = "PCT_CHANGE_1M", _("1-Month Percent Change")
    PCT_CHANGE_YOY = "PCT_CHANGE_YOY", _("Year-over-Year Percent Change")
    LOG_RETURN = "LOG_RETURN", _("Logarithmic Return")
    SPREAD_DIFF = "SPREAD_DIFF", _("Crack/Crush/Calendar Spread Difference")


class VariableMaster(UUIDModel, TimeStampedModel):
    """
    Canonical reference model for an individual measurable attribute or observable
    time series within a commodity market dataset.
    """

    code = models.CharField(
        max_length=80,
        unique=True,
        db_index=True,
        help_text="Canonical unique metric code (e.g. EIA_CRUDE_CUSHING_STOCKS, WASDE_CORN_US_ENDING_STOCKS).",
    )
    name = models.CharField(
        max_length=150,
        help_text="Full institutional metric title.",
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed methodology, scope, and measurement parameters.",
    )
    dataset = models.ForeignKey(
        "datasets.DatasetMaster",
        on_delete=models.CASCADE,
        related_name="variables",
        help_text="Parent dataset publishing or containing this variable series.",
    )
    domain = models.ForeignKey(
        "metadata.DataDomainMaster",
        on_delete=models.PROTECT,
        related_name="variables",
        help_text="Parent data domain taxonomy classification.",
    )
    commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="variables",
        help_text="Direct physical commodity anchor (null for cross-asset or macro series).",
    )
    unit = models.ForeignKey(
        "metadata.UnitMaster",
        on_delete=models.PROTECT,
        related_name="variables",
        help_text="Canonical physical or financial unit of measure (e.g. BBL, BU, MT, USD_BBL).",
    )
    data_type = models.CharField(
        max_length=30,
        choices=VariableDataType.choices,
        default=VariableDataType.DECIMAL,
        help_text="Underlying value data representation type.",
    )
    aggregation_method = models.CharField(
        max_length=20,
        choices=AggregationMethod.choices,
        default=AggregationMethod.LAST,
        help_text="Mathematical temporal resampling logic (LAST for stocks, SUM for flows, AVG for rates).",
    )
    seasonal_adjustment = models.CharField(
        max_length=30,
        choices=SeasonalAdjustment.choices,
        default=SeasonalAdjustment.UNADJUSTED,
        help_text="Seasonal adjustment status (NSA vs SA).",
    )
    default_transformation = models.CharField(
        max_length=30,
        choices=DisplayTransformation.choices,
        default=DisplayTransformation.RAW_LEVEL,
        help_text="Default analytical transformation hint for charting and LLM narratives.",
    )
    is_benchmark = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this variable is a headline benchmark indicator.",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this variable is actively observed and ingested.",
    )
    display_order = models.PositiveIntegerField(
        default=100,
        help_text="Sorting order in dashboards and analytical tables.",
    )

    class Meta:
        db_table = "variables_master"
        ordering = ["display_order", "code"]
        verbose_name = _("Variable Master")
        verbose_name_plural = _("Variable Master Catalog")

    def __str__(self) -> str:
        comm_str = f" [{self.commodity.code}]" if self.commodity else ""
        return f"{self.code}: {self.name}{comm_str} ({self.unit.code})"
