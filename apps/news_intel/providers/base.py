"""
Abstract base classes and DTOs for the News & Market Intelligence Provider layer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


@dataclass(frozen=True)
class RawNewsCommodityTagDTO:
    """Normalized DTO for commodity tagging associated with a news article."""
    commodity_code: str
    relevance_score: Decimal = Decimal("1.000")
    is_primary: bool = False
    commodity_sentiment: str = "NEUTRAL"
    commodity_sentiment_score: Decimal = Decimal("0.000")
    matched_keywords: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RawNewsArticleDTO:
    """Normalized DTO for news articles ingested from external wires or mock feeds."""
    title: str
    summary: str
    published_at_utc: datetime
    source_name: str
    source_url: str = ""
    content: str = ""
    author: str = ""
    overall_sentiment_score: Decimal = Decimal("0.000")
    overall_sentiment_label: str = "NEUTRAL"
    confidence_score: Decimal = Decimal("0.850")
    is_breaking: bool = False
    primary_commodity_code: Optional[str] = None
    tags: List[RawNewsCommodityTagDTO] = field(default_factory=list)
    catalyst_event_name: Optional[str] = None


@dataclass(frozen=True)
class RawCatalystEventDTO:
    """Normalized DTO for scheduled market catalysts and expectations."""
    name: str
    event_type: str
    impact_level: str
    scheduled_datetime_utc: datetime
    source_agency: str
    status: str = "SCHEDULED"
    period_covered: str = ""
    primary_commodity_code: Optional[str] = None
    affected_commodity_codes: List[str] = field(default_factory=list)
    consensus_expectation: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None
    prior_value: Optional[Decimal] = None
    unit_symbol: Optional[str] = None
    surprise_magnitude: Optional[Decimal] = None
    surprise_direction: str = "UNAVAILABLE"
    notes: str = ""


class BaseNewsProvider(ABC):
    """Abstract interface defining the contract for news & catalyst calendar providers."""

    @abstractmethod
    def get_catalyst_events(
        self,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        commodity_code: Optional[str] = None,
    ) -> List[RawCatalystEventDTO]:
        """Fetch scheduled market catalyst events across primary and affected commodities."""
        pass

    @abstractmethod
    def get_news_articles(
        self,
        limit: int = 50,
        commodity_code: Optional[str] = None,
    ) -> List[RawNewsArticleDTO]:
        """Fetch news articles with multi-product tagging and sentiment attributes."""
        pass
