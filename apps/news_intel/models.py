"""
News & Market Intelligence Domain Models.

Implements the macroeconomic catalyst calendar and multi-product news intelligence layer:
- MarketCatalystEvent: Official point-in-time publication schedule (OPEC, WASDE, FOMC, EIA)
- NewsArticle: Real-time and historical news headlines with content hashing and sentiment
- NewsCommodityTag: Many-to-many link between an article and multiple commodities with per-product relevance and sentiment
"""
from decimal import Decimal
from django.db import models
from apps.core.models import UUIDModel, PointInTimeModel, TimeStampedModel


class EventType(models.TextChoices):
    POLICY_OPEC = "POLICY_OPEC", "OPEC & OPEC+ Policy"
    GOVERNMENT_WASDE = "GOVERNMENT_WASDE", "USDA WASDE Crop Report"
    MACRO_CENTRAL_BANK = "MACRO_CENTRAL_BANK", "Central Bank & Interest Rates"
    INVENTORY_EIA = "INVENTORY_EIA", "EIA Storage & Inventories"
    REGULATORY_CFTC = "REGULATORY_CFTC", "CFTC Regulatory & COT"
    WEATHER_ANOMALY = "WEATHER_ANOMALY", "Severe Weather & Crop Progress"
    GEOPOLITICAL = "GEOPOLITICAL", "Geopolitical & Supply Disruption"


class ImpactLevel(models.TextChoices):
    HIGH = "HIGH", "High Impact"
    MEDIUM = "MEDIUM", "Medium Impact"
    LOW = "LOW", "Low Impact"


class EventStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    OCCURRED = "OCCURRED", "Occurred"
    POSTPONED = "POSTPONED", "Postponed"
    CANCELLED = "CANCELLED", "Cancelled"


class SurpriseDirection(models.TextChoices):
    BULLISH_SURPRISE = "BULLISH_SURPRISE", "Bullish Surprise"
    BEARISH_SURPRISE = "BEARISH_SURPRISE", "Bearish Surprise"
    IN_LINE = "IN_LINE", "In-Line with Consensus"
    UNAVAILABLE = "UNAVAILABLE", "Unavailable"


class SentimentLabel(models.TextChoices):
    STRONG_BULLISH = "STRONG_BULLISH", "Strong Bullish"
    MODERATE_BULLISH = "MODERATE_BULLISH", "Moderate Bullish"
    NEUTRAL = "NEUTRAL", "Neutral"
    MODERATE_BEARISH = "MODERATE_BEARISH", "Moderate Bearish"
    STRONG_BEARISH = "STRONG_BEARISH", "Strong Bearish"


class MarketCatalystEvent(UUIDModel, PointInTimeModel, TimeStampedModel):
    """
    Official scheduled macroeconomic, government, and industry catalyst events.
    Tracks pre-event consensus expectations, actual release outcomes, and market surprises.
    """
    name = models.CharField(
        max_length=200,
        help_text="Official name of the event or report release",
    )
    event_type = models.CharField(
        max_length=32,
        choices=EventType.choices,
        db_index=True,
        help_text="Categorical domain of the market catalyst",
    )
    impact_level = models.CharField(
        max_length=16,
        choices=ImpactLevel.choices,
        default=ImpactLevel.HIGH,
        db_index=True,
        help_text="Estimated market volatility impact intensity",
    )
    scheduled_datetime_utc = models.DateTimeField(
        db_index=True,
        help_text="Exact scheduled UTC announcement or publication timestamp",
    )
    status = models.CharField(
        max_length=16,
        choices=EventStatus.choices,
        default=EventStatus.SCHEDULED,
        db_index=True,
        help_text="Current execution status of the event",
    )
    primary_commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_catalyst_events",
        help_text="Primary benchmark commodity most directly impacted",
    )
    affected_commodities = models.ManyToManyField(
        "commodities.CommodityMaster",
        blank=True,
        related_name="affected_catalyst_events",
        help_text="All commodities affected by this macroeconomic release",
    )
    source_agency = models.CharField(
        max_length=100,
        help_text="Issuing agency or organization (e.g. 'OPEC Secretariat', 'USDA WAOB', 'EIA', 'Federal Reserve')",
    )
    period_covered = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Reporting period covered (e.g. 'September 2026', 'Week Ending Sep 25')",
    )
    consensus_expectation = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Survey median consensus expectation prior to release",
    )
    actual_value = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Officially released actual figure",
    )
    prior_value = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Prior period reported figure",
    )
    unit = models.ForeignKey(
        "metadata.UnitMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Unit of measure for expectation/actual metrics",
    )
    surprise_magnitude = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Numerical delta: Actual minus Consensus",
    )
    surprise_direction = models.CharField(
        max_length=24,
        choices=SurpriseDirection.choices,
        default=SurpriseDirection.UNAVAILABLE,
        db_index=True,
        help_text="Economic market impact interpretation of the surprise delta",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional qualitative commentary or release context",
    )

    class Meta:
        ordering = ["-scheduled_datetime_utc"]
        verbose_name = "Market Catalyst Event"
        verbose_name_plural = "Market Catalyst Events"

    def __str__(self):
        return f"{self.name} [{self.scheduled_datetime_utc.strftime('%Y-%m-%d %H:%M')} UTC]"


class NewsArticle(UUIDModel, PointInTimeModel, TimeStampedModel):
    """
    Standardized news article and wire headline observation.
    Captures content provenance, SHA-256 deduplication, sentiment polarity, and multi-commodity linkages.
    """
    title = models.CharField(
        max_length=300,
        help_text="Article headline / title",
    )
    summary = models.TextField(
        help_text="Concise executive summary or introductory excerpt",
    )
    content = models.TextField(
        blank=True,
        default="",
        help_text="Full article text or wire transcript (optional)",
    )
    source_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Originating publisher or news agency (e.g. 'Reuters', 'Bloomberg', 'Platts', 'USDA')",
    )
    source_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Canonical link to the online article",
    )
    published_at_utc = models.DateTimeField(
        db_index=True,
        help_text="Official publication timestamp in UTC",
    )
    author = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Byline author or editorial desk",
    )
    content_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA-256 hash of title and published timestamp for idempotent deduplication",
    )
    overall_sentiment_score = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Normalized directional sentiment score (-1.000 to +1.000)",
    )
    overall_sentiment_label = models.CharField(
        max_length=24,
        choices=SentimentLabel.choices,
        default=SentimentLabel.NEUTRAL,
        db_index=True,
        help_text="Overall categorical sentiment polarity classification",
    )
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal("0.850"),
        help_text="Confidence probability of the sentiment classification (0.0 to 1.0)",
    )
    is_breaking = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flag marking high-urgency breaking market development",
    )
    primary_commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_news_articles",
        help_text="Highest-weighted primary commodity affected",
    )
    commodities = models.ManyToManyField(
        "commodities.CommodityMaster",
        through="NewsCommodityTag",
        related_name="news_articles",
        help_text="All physical commodities affected by this article",
    )
    catalyst_event = models.ForeignKey(
        MarketCatalystEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news_articles",
        help_text="Associated official catalyst release event if reporting on a scheduled release",
    )

    class Meta:
        ordering = ["-published_at_utc"]
        verbose_name = "News Article"
        verbose_name_plural = "News Articles"

    def __str__(self):
        return f"{self.title[:60]}... [{self.source_name}]"


class NewsCommodityTag(models.Model):
    """
    Through model establishing explicit many-to-many linkages between a NewsArticle
    and multiple CommodityMaster instances with per-commodity relevance and sentiment.
    """
    article = models.ForeignKey(
        NewsArticle,
        on_delete=models.CASCADE,
        related_name="commodity_tags",
        help_text="Parent news article",
    )
    commodity = models.ForeignKey(
        "commodities.CommodityMaster",
        on_delete=models.CASCADE,
        related_name="news_tags",
        help_text="Target affected physical commodity",
    )
    relevance_score = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal("1.000"),
        help_text="Weighted relevance of this article to this commodity (0.000 to 1.000)",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Flag indicating whether this commodity is the primary subject of the article",
    )
    commodity_sentiment = models.CharField(
        max_length=24,
        choices=SentimentLabel.choices,
        default=SentimentLabel.NEUTRAL,
        help_text="Directional sentiment impact specific to this individual commodity",
    )
    commodity_sentiment_score = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Specific sentiment polarity score for this commodity (-1.000 to +1.000)",
    )
    matched_keywords = models.JSONField(
        default=list,
        blank=True,
        help_text="Exact physical taxonomy keywords and stems that triggered the match",
    )

    class Meta:
        unique_together = ("article", "commodity")
        verbose_name = "News Commodity Tag"
        verbose_name_plural = "News Commodity Tags"

    def __str__(self):
        return f"{self.article.title[:30]} ➔ {self.commodity.code} ({self.commodity_sentiment})"
