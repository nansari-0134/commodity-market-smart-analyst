"""
Data models for AI Market Narratives, Executive Briefings, and Hybrid Context Synthesis.
"""
from django.db import models
from django.utils import timezone
from apps.core.models import UUIDModel, PointInTimeModel
from apps.commodities.models import CommodityMaster

REGULATORY_COMPLIANCE_DISCLAIMER = (
    "STANDARD REGULATORY COMPLIANCE NOTICE: This automated market briefing is strictly an "
    "analytical research, quantitative surveillance, and intelligence workflow tool. It does "
    "NOT constitute financial, investment, or trading advice, nor an offer, solicitation, or "
    "recommendation to buy, sell, or hold any commodity derivative, futures contract, or security. "
    "All quantitative metrics, forward curve models, and narrative syntheses are generated "
    "systematically and carry inherent market risks."
)


class NarrativeType(models.TextChoices):
    MORNING_BRIEF = "MORNING_BRIEF", "Morning Executive Briefing"
    EXECUTIVE_FLASH = "EXECUTIVE_FLASH", "Executive Flash"
    SUPPLY_DEMAND = "SUPPLY_DEMAND", "Supply/Demand Balance Commentary"
    RISK_ALERT = "RISK_ALERT", "Systemic Risk & Divergence Alert"
    OUTLIER_DIVERGENCE = "OUTLIER_DIVERGENCE", "Quantitative Outlier Discovery"


class NarrativeStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Published"
    ARCHIVED = "ARCHIVED", "Archived"


class MarketNarrative(UUIDModel, PointInTimeModel):
    """
    Point-in-time immutable record of an AI-synthesized market narrative.
    
    Guarantees strict adherence to:
    - Directive 2: Point-in-time correctness (frozen availability_time).
    - Directive 3: Deterministic arithmetic precedes LLM reasoning (evidence snapshot saved).
    - Directive 4: Standard regulatory compliance notice.
    """
    commodity = models.ForeignKey(
        CommodityMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="narratives",
        help_text="Target commodity or null for cross-commodity / macro deck",
    )
    narrative_type = models.CharField(
        max_length=32,
        choices=NarrativeType.choices,
        default=NarrativeType.MORNING_BRIEF,
        db_index=True,
    )
    headline = models.CharField(
        max_length=255,
        help_text="Institutional headline synthesizing key market dynamic",
    )
    executive_summary = models.TextField(
        help_text="2-3 sentence high-level executive summary",
    )
    market_context_body = models.TextField(
        help_text="Structured Markdown narrative covering fundamentals, curves, and quantitative posture",
    )
    key_bullet_points = models.JSONField(
        default=list,
        blank=True,
        help_text="High-conviction quantitative bullets / takeaways",
    )
    risk_factors = models.JSONField(
        default=list,
        blank=True,
        help_text="Surveillance risk vectors, asymmetries, and catalyst triggers",
    )
    evidence_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Frozen ground-truth quantitative state consumed by LLM",
    )
    llm_provider = models.CharField(
        max_length=64,
        default="static",
        db_index=True,
        help_text="Identifier of the LLM provider adapter (e.g., gemini, claude, openai, ollama, static)",
    )
    llm_model = models.CharField(
        max_length=64,
        default="static-engine",
        help_text="Underlying model identifier (e.g. gemini-2.0-flash, claude-3-5-sonnet)",
    )
    prompt_tokens = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Token count of prompt context",
    )
    completion_tokens = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Token count of generated response",
    )
    status = models.CharField(
        max_length=16,
        choices=NarrativeStatus.choices,
        default=NarrativeStatus.PUBLISHED,
        db_index=True,
    )
    compliance_disclaimer = models.TextField(
        default=REGULATORY_COMPLIANCE_DISCLAIMER,
        help_text="Mandatory regulatory disclaimer automatically attached to report",
    )

    class Meta:
        ordering = ["-availability_time"]
        verbose_name = "Market Narrative"
        verbose_name_plural = "Market Narratives"
        indexes = [
            models.Index(fields=["commodity", "narrative_type", "availability_time"]),
            models.Index(fields=["narrative_type", "status"]),
        ]

    def __str__(self) -> str:
        symbol = self.commodity.code if self.commodity else "MACRO"
        return f"[{symbol}] {self.get_narrative_type_display()} - {self.headline[:40]}"
