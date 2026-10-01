"""
Comprehensive Automated Test Suite for News Intelligence, Sentiment & Market Catalyst Calendar (Phase 12).

Tests:
1. MarketCatalystEvent models with primary and multi-affected commodities.
2. NewsArticle & NewsCommodityTag models with multi-product linkages, relevance scores, and sentiment.
3. Content deduplication via SHA-256 hashing.
4. StaticNewsProvider and RSSNewsProvider provider strategy.
5. CommodityEntityLinker domain taxonomy and cross-commodity propagation.
6. LexiconSentimentEngine deterministic polarity scoring and negation handling.
7. CatalystSurpriseEngine consensus delta and directional impact evaluation.
8. ingest_news_intel management command execution.
9. REST API endpoints under /api/news/ (catalysts, articles, summary, upcoming, breaking).
"""

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from django.core.management import call_command
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.commodities.models import CommodityMaster, CommoditySector
from apps.exchanges.models import ExchangeMaster
from apps.metadata.models import UnitMaster, UnitType
from apps.news_intel.models import (
    EventType,
    ImpactLevel,
    EventStatus,
    SurpriseDirection,
    SentimentLabel,
    MarketCatalystEvent,
    NewsArticle,
    NewsCommodityTag,
)
from apps.news_intel.providers.base import (
    RawCatalystEventDTO,
    RawNewsArticleDTO,
    RawNewsCommodityTagDTO,
)
from apps.news_intel.providers.static_data import StaticNewsProvider
from apps.news_intel.providers.rss_provider import RSSNewsProvider
from apps.news_intel.providers.factory import get_news_provider
from apps.news_intel.services.entity_linker import CommodityEntityLinker
from apps.news_intel.services.sentiment_engine import LexiconSentimentEngine
from apps.news_intel.services.surprise_engine import CatalystSurpriseEngine


@pytest.fixture
def exchange(db):
    exch, _ = ExchangeMaster.objects.get_or_create(
        code="NYMEX_TEST",
        defaults={"name": "New York Mercantile Exchange Test", "country": "USA", "timezone": "America/New_York"},
    )
    return exch


@pytest.fixture
def unit_bbl(db):
    u, _ = UnitMaster.objects.get_or_create(
        code="BBL_TEST",
        defaults={"name": "Barrels Test", "symbol": "bbl", "unit_type": UnitType.VOLUME, "conversion_factor": Decimal("1.0")},
    )
    return u


@pytest.fixture
def commodities(db, exchange, unit_bbl):
    crude, _ = CommodityMaster.objects.get_or_create(
        code="CL_TEST",
        defaults={
            "name": "Crude Oil Test",
            "sector": CommoditySector.ENERGY,
            "primary_exchange": exchange,
            "base_unit": unit_bbl,
            "pricing_unit": unit_bbl,
            "standard_lot_unit": unit_bbl,
        },
    )
    brent, _ = CommodityMaster.objects.get_or_create(
        code="BRENT_TEST",
        defaults={
            "name": "Brent Crude Test",
            "sector": CommoditySector.ENERGY,
            "primary_exchange": exchange,
            "base_unit": unit_bbl,
            "pricing_unit": unit_bbl,
            "standard_lot_unit": unit_bbl,
        },
    )
    heating_oil, _ = CommodityMaster.objects.get_or_create(
        code="HO_TEST",
        defaults={
            "name": "Heating Oil Test",
            "sector": CommoditySector.ENERGY,
            "primary_exchange": exchange,
            "base_unit": unit_bbl,
            "pricing_unit": unit_bbl,
            "standard_lot_unit": unit_bbl,
        },
    )
    return crude, brent, heating_oil


def ensure_seed_commodities():
    """Ensure standard benchmark commodities exist in test database for command & API tests."""
    call_command("seed_metadata")
    call_command("seed_exchanges", skip_api_holidays=True)
    call_command("seed_commodities")


# =========================================================================
# 1. Models & Multi-Commodity Linkage Tests
# =========================================================================

@pytest.mark.django_db
class TestNewsIntelModels:
    def test_catalyst_event_creation(self, commodities, unit_bbl):
        cl, brent, ho = commodities
        event = MarketCatalystEvent.objects.create(
            name="OPEC+ Joint Ministerial Monitoring Meeting",
            event_type=EventType.POLICY_OPEC,
            impact_level=ImpactLevel.HIGH,
            scheduled_datetime_utc=datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc),
            status=EventStatus.SCHEDULED,
            primary_commodity=cl,
            source_agency="OPEC Secretariat",
            period_covered="Q4 2026",
            consensus_expectation=Decimal("-2.2000"),
            unit=unit_bbl,
            surprise_direction=SurpriseDirection.UNAVAILABLE,
        )
        event.affected_commodities.set([cl, brent, ho])

        assert event.id is not None
        assert event.primary_commodity == cl
        assert event.affected_commodities.count() == 3
        assert "OPEC+" in str(event)

    def test_news_article_multi_commodity_tags(self, commodities):
        """
        Verify that a single news article can link to multiple commodities
        with per-commodity relevance scores and specific sentiment polarities.
        """
        cl, brent, ho = commodities
        title = "OPEC+ Extends Production Cuts; Crude Rallies while Distillates Follow"
        published_at = datetime(2026, 10, 1, 9, 30, tzinfo=timezone.utc)
        content_hash = hashlib.sha256(f"{title}:{published_at.isoformat()}".encode("utf-8")).hexdigest()

        article = NewsArticle.objects.create(
            title=title,
            summary="OPEC ministers agreed to keep 2.2 mbpd voluntary cuts through year end.",
            source_name="Reuters Energy",
            published_at_utc=published_at,
            content_hash=content_hash,
            overall_sentiment_score=Decimal("0.750"),
            overall_sentiment_label=SentimentLabel.STRONG_BULLISH,
            is_breaking=True,
            primary_commodity=cl,
        )

        # Tag 1: Crude Oil (Primary, relevance 1.0, Strong Bullish)
        tag_cl = NewsCommodityTag.objects.create(
            article=article,
            commodity=cl,
            relevance_score=Decimal("1.000"),
            is_primary=True,
            commodity_sentiment=SentimentLabel.STRONG_BULLISH,
            commodity_sentiment_score=Decimal("0.850"),
            matched_keywords=["opec", "crude", "production cuts"],
        )

        # Tag 2: Brent Crude (Secondary, relevance 0.9, Strong Bullish)
        tag_brent = NewsCommodityTag.objects.create(
            article=article,
            commodity=brent,
            relevance_score=Decimal("0.900"),
            is_primary=False,
            commodity_sentiment=SentimentLabel.STRONG_BULLISH,
            commodity_sentiment_score=Decimal("0.800"),
            matched_keywords=["opec", "crude"],
        )

        # Tag 3: Heating Oil (Secondary, relevance 0.65, Moderate Bullish)
        tag_ho = NewsCommodityTag.objects.create(
            article=article,
            commodity=ho,
            relevance_score=Decimal("0.650"),
            is_primary=False,
            commodity_sentiment=SentimentLabel.MODERATE_BULLISH,
            commodity_sentiment_score=Decimal("0.450"),
            matched_keywords=["distillates"],
        )

        assert article.commodity_tags.count() == 3
        assert article.commodities.count() == 3
        assert tag_cl.is_primary is True
        assert tag_brent.is_primary is False
        assert tag_ho.commodity_sentiment_score == Decimal("0.450")
        assert "CL_TEST" in str(tag_cl)

    def test_news_article_deduplication_hash(self, commodities):
        """Verify unique constraint on content_hash prevents duplicate ingestion."""
        cl, _, _ = commodities
        content_hash = "unique_sha256_hash_12345"

        NewsArticle.objects.create(
            title="Duplicate Title Test 1",
            summary="Summary 1",
            source_name="Wire",
            published_at_utc=datetime.now(timezone.utc),
            content_hash=content_hash,
            primary_commodity=cl,
        )

        with pytest.raises(IntegrityError):
            NewsArticle.objects.create(
                title="Duplicate Title Test 2",
                summary="Summary 2",
                source_name="Wire",
                published_at_utc=datetime.now(timezone.utc),
                content_hash=content_hash,
                primary_commodity=cl,
            )


# =========================================================================
# 2. Providers & Factory Tests
# =========================================================================

class TestNewsProviders:
    def test_static_news_provider_events(self):
        provider = StaticNewsProvider()
        events = provider.get_catalyst_events()
        assert len(events) >= 5

        # Test filtering by commodity (checks both primary and affected)
        cl_events = provider.get_catalyst_events(commodity_code="CL")
        assert len(cl_events) >= 2
        for e in cl_events:
            assert e.primary_commodity_code == "CL" or "CL" in e.affected_commodity_codes

    def test_static_news_provider_articles(self):
        provider = StaticNewsProvider()
        articles = provider.get_news_articles(limit=5)
        assert len(articles) <= 5

        # Multi-commodity tag verification
        first_art = articles[0]
        assert len(first_art.tags) > 0
        assert first_art.overall_sentiment_score != Decimal("0.000")

    def test_rss_provider_fallback(self):
        # Point to unreachable URL to test fallback guarantee
        provider = RSSNewsProvider(feeds=[{"name": "Bad Feed", "url": "http://127.0.0.1:9999/nonexistent.xml"}])
        articles = provider.get_news_articles(limit=10)
        assert len(articles) > 0  # Successfully fell back to static benchmark seeds

    def test_provider_factory(self, settings):
        settings.NEWS_PROVIDER = "static"
        p_static = get_news_provider()
        assert isinstance(p_static, StaticNewsProvider)

        settings.NEWS_PROVIDER = "rss"
        p_rss = get_news_provider()
        assert isinstance(p_rss, RSSNewsProvider)


# =========================================================================
# 3. Core Intelligence Services Tests
# =========================================================================

class TestCoreServices:
    def test_entity_linker_direct_and_cross_link(self):
        linker = CommodityEntityLinker()
        text = "OPEC+ ministers decided to extend voluntary oil supply cuts to bolster light sweet crude and brent prices."
        matches = linker.link_entities(text)

        codes = [m.commodity_code for m in matches]
        assert "CL" in codes
        assert "BRENT" in codes
        # Direct matched commodity should be primary
        primary = next(m for m in matches if m.is_primary)
        assert primary.commodity_code in ["CL", "BRENT"]
        assert primary.relevance_score >= Decimal("0.500")

    def test_entity_linker_empty_and_threshold(self):
        linker = CommodityEntityLinker()
        assert linker.link_entities("") == []
        assert linker.link_entities("random irrelevant financial text without commodities") == []

    def test_sentiment_engine_bullish(self):
        engine = LexiconSentimentEngine()
        text = "EIA confirms huge crude oil inventory drawdown; gasoline and distillate demand surges to record highs."
        res = engine.score_text(text)
        assert res.score > Decimal("0.200")
        assert res.label in ["STRONG_BULLISH", "MODERATE_BULLISH"]
        assert res.confidence > Decimal("0.700")

    def test_sentiment_engine_bearish(self):
        engine = LexiconSentimentEngine()
        text = "Record harvest triggers grain supply glut; bumper crop causes corn prices to plummet and slump."
        res = engine.score_text(text)
        assert res.score < Decimal("-0.200")
        assert res.label in ["STRONG_BEARISH", "MODERATE_BEARISH"]

    def test_sentiment_engine_negation(self):
        engine = LexiconSentimentEngine()
        text = "OPEC ministers are unlikely to cut production despite market weakness."
        res = engine.score_text(text)
        # Negation of 'cut' should flip or damp the score
        assert res.score <= Decimal("0.100")

    def test_surprise_engine_inventory_eia(self):
        # Consensus: -1.0 MMBBL draw, Actual: -4.5 MMBBL draw -> Delta: -3.5 (larger draw = BULLISH)
        mag, direction = CatalystSurpriseEngine.evaluate_surprise(
            actual_value=Decimal("-4.5000"),
            consensus_expectation=Decimal("-1.0000"),
            event_type=EventType.INVENTORY_EIA,
            event_name="EIA Weekly Petroleum Status Report",
        )
        assert mag == Decimal("-3.5000")
        assert direction == SurpriseDirection.BULLISH_SURPRISE

        # Consensus: 50 Bcf injection, Actual: 75 Bcf injection -> Delta: +25 (larger build = BEARISH)
        mag2, direction2 = CatalystSurpriseEngine.evaluate_surprise(
            actual_value=Decimal("75.0000"),
            consensus_expectation=Decimal("50.0000"),
            event_type=EventType.INVENTORY_EIA,
            event_name="EIA Natural Gas Underground Storage",
        )
        assert mag2 == Decimal("25.0000")
        assert direction2 == SurpriseDirection.BEARISH_SURPRISE

    def test_surprise_engine_wasde_crop_yield(self):
        # Consensus: 182.0 bu/acre, Actual: 179.5 bu/acre -> Delta: -2.5 (lower yield = BULLISH)
        mag, direction = CatalystSurpriseEngine.evaluate_surprise(
            actual_value=Decimal("179.5000"),
            consensus_expectation=Decimal("182.0000"),
            event_type=EventType.GOVERNMENT_WASDE,
            event_name="USDA WASDE Corn Production",
        )
        assert mag == Decimal("-2.5000")
        assert direction == SurpriseDirection.BULLISH_SURPRISE

    def test_surprise_engine_central_bank_rates(self):
        # Fed cuts rate by more than expected: Consensus: 4.75, Actual: 4.50 -> BULLISH
        mag, direction = CatalystSurpriseEngine.evaluate_surprise(
            actual_value=Decimal("4.5000"),
            consensus_expectation=Decimal("4.7500"),
            event_type=EventType.MACRO_CENTRAL_BANK,
            event_name="FOMC Interest Rate Decision",
        )
        assert mag == Decimal("-0.2500")
        assert direction == SurpriseDirection.BULLISH_SURPRISE


# =========================================================================
# 4. Ingestion Command & Database End-to-End Tests
# =========================================================================

@pytest.mark.django_db
class TestNewsIntelIngestion:
    def test_ingest_news_intel_command(self):
        ensure_seed_commodities()
        # Execute management command
        call_command("ingest_news_intel", "--clear")

        assert MarketCatalystEvent.objects.count() >= 5
        assert NewsArticle.objects.count() >= 5
        assert NewsCommodityTag.objects.count() >= 15

        # Check multi-commodity tags on a representative article
        art = NewsArticle.objects.filter(commodity_tags__commodity__code="BRENT").first()
        assert art is not None
        assert art.commodity_tags.count() >= 2


# =========================================================================
# 5. REST API Suite Tests
# =========================================================================

@pytest.mark.django_db
class TestNewsIntelAPI:
    def setup_method(self):
        ensure_seed_commodities()
        call_command("ingest_news_intel", "--clear")
        self.client = APIClient()

    def test_catalysts_endpoint(self):
        resp = self.client.get("/api/news/catalysts/")
        assert resp.status_code == 200
        data = resp.data["results"] if isinstance(resp.data, dict) and "results" in resp.data else resp.data
        assert len(data) >= 5

        # Verify affected commodities field in serialized output
        first = data[0]
        assert "affected_commodities" in first
        assert isinstance(first["affected_commodities"], list)

    def test_catalysts_filter_by_commodity(self):
        resp = self.client.get("/api/news/catalysts/?commodity=CL")
        assert resp.status_code == 200
        data = resp.data["results"] if isinstance(resp.data, dict) and "results" in resp.data else resp.data
        assert len(data) >= 1

    def test_catalysts_upcoming_action(self):
        resp = self.client.get("/api/news/catalysts/upcoming/?days=30")
        assert resp.status_code == 200
        assert isinstance(resp.data, list)

    def test_articles_endpoint(self):
        resp = self.client.get("/api/news/articles/")
        assert resp.status_code == 200
        data = resp.data["results"] if isinstance(resp.data, dict) and "results" in resp.data else resp.data
        assert len(data) >= 5

        first = data[0]
        assert "commodity_tags" in first
        assert len(first["commodity_tags"]) >= 1

    def test_articles_multi_commodity_filter(self):
        # Test filtering by a secondary linked commodity like BRENT or HO
        resp = self.client.get("/api/news/articles/?commodity=BRENT")
        assert resp.status_code == 200
        data = resp.data["results"] if isinstance(resp.data, dict) and "results" in resp.data else resp.data
        assert len(data) >= 1

    def test_articles_breaking_action(self):
        resp = self.client.get("/api/news/articles/breaking/")
        assert resp.status_code == 200
        data = resp.data
        for item in data:
            assert item["is_breaking"] is True

    def test_news_sentiment_summary(self):
        resp = self.client.get("/api/news/summary/")
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) >= 1
        first = resp.data[0]
        assert "commodity_code" in first
        assert "average_sentiment_score" in first
        assert "dominant_sentiment_label" in first
        assert "article_count" in first
