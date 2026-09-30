"""
Quantitative Research & Discovery Registry Models.

Enforces:
- Section 5.11 & 18: Discovery Registry for validated relationships, regimes, event reactions, and anomalies
- Point-in-time auditability and provenance (Section 15)
- JSON evidence package persistence for downstream LLM synthesis
"""
from django.db import models
from apps.core.models import UUIDModel, PointInTimeModel, TimeStampedModel, DataQualityStatus


class DiscoveryType(models.TextChoices):
    """Categorical classification of validated quantitative findings."""
    REGIME_CHANGE = "REGIME_CHANGE", "Market Regime Transition"
    DIVERGENCE_ALERT = "DIVERGENCE_ALERT", "Cross-Domain Divergence Alert"
    ANOMALY = "ANOMALY", "Statistical Price/Volume/Spread Anomaly"
    COINTEGRATION_PAIR = "COINTEGRATION_PAIR", "Cointegration & Mean-Reverting Spread"
    SEASONAL_TENDENCY = "SEASONAL_TENDENCY", "Directional Seasonal Window"
    VOLATILITY_PEAK = "VOLATILITY_PEAK", "Forward Volatility Peak Window"
    SPREAD_DISLOCATION = "SPREAD_DISLOCATION", "Processing Spread Dislocation"


class DiscoveryRegistry(UUIDModel, PointInTimeModel, TimeStampedModel):
    """
    Audit registry for validated quantitative relationships, empirical anomalies,
    and regime states discovered by the Quantitative Engine.
    """
    discovery_type = models.CharField(
        max_length=32,
        choices=DiscoveryType.choices,
        db_index=True,
        help_text="Classification of quantitative discovery",
    )
    title = models.CharField(
        max_length=255,
        help_text="Canonical discovery title (e.g. 'CL-BRENT Spread Mean-Reversion Candidate')",
    )
    commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.CASCADE,
        related_name="quant_discoveries",
        help_text="Primary benchmark commodity analyzed",
    )
    related_commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_quant_discoveries",
        help_text="Secondary commodity in pairs/spreads (optional)",
    )
    as_of_date = models.DateField(
        db_index=True,
        help_text="Market date of the discovery",
    )
    confidence_score = models.FloatField(
        default=1.0,
        help_text="Normalized statistical confidence / correlation strength (0.0 to 1.0)",
    )
    is_statistically_significant = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Flag indicating p-value < 0.05 or t-stat > 2.0",
    )
    p_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Statistical significance p-value from hypothesis test",
    )
    t_statistic = models.FloatField(
        null=True,
        blank=True,
        help_text="Test statistic (t-stat, ADF tau, or z-score)",
    )
    sample_size = models.PositiveIntegerField(
        default=252,
        help_text="Number of historical observation bars in test sample",
    )
    lookback_window = models.CharField(
        max_length=32,
        default="252D",
        help_text="Lookback tenure (e.g. '30D', '90D', '252D', '5Y')",
    )
    evidence_payload = models.JSONField(
        default=dict,
        help_text="Structured discovery details (beta, half-life, z-score, regime label)",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this finding is currently active and un-invalidated",
    )
    data_quality = models.CharField(
        max_length=16,
        choices=DataQualityStatus.choices,
        default=DataQualityStatus.VALID,
        help_text="Input data quality audit state",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Methodology notes, economic rationale, and invalidation criteria",
    )

    class Meta:
        ordering = ["-as_of_date", "-confidence_score"]
        indexes = [
            models.Index(fields=["commodity", "as_of_date"]),
            models.Index(fields=["discovery_type", "as_of_date"]),
            models.Index(fields=["is_active", "is_statistically_significant"]),
        ]

    def __str__(self) -> str:
        return f"[{self.discovery_type}] {self.commodity.code} @ {self.as_of_date}: {self.title}"


class EvidencePackageSnapshot(UUIDModel, PointInTimeModel, TimeStampedModel):
    """
    Immutable historical snapshot of the complete Quantitative Evidence Package (Section 5.12).
    Used for audit trails, out-of-sample backtesting, and grounding LLM research briefs.
    """
    commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.CASCADE,
        related_name="evidence_snapshots",
        help_text="Primary benchmark commodity",
    )
    as_of_date = models.DateField(
        db_index=True,
        help_text="Market date of the evidence package",
    )
    engine_version = models.CharField(
        max_length=32,
        default="1.0.0",
        help_text="Semantic version of the Quantitative Engine",
    )
    package_payload = models.JSONField(
        help_text="Complete JSON evidence package adhering to Section 5.12 Pydantic schema",
    )

    class Meta:
        ordering = ["-as_of_date", "commodity"]
        indexes = [
            models.Index(fields=["commodity", "as_of_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["commodity", "as_of_date", "engine_version"],
                name="unique_evidence_snapshot",
            )
        ]

    def __str__(self) -> str:
        return f"EvidencePackage {self.commodity.code} @ {self.as_of_date} (v{self.engine_version})"
