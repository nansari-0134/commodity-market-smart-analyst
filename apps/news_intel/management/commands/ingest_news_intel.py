"""
Management command to ingest macroeconomic catalysts, news articles, and multi-product tags.

Executes:
1. Ingestion of scheduled and historical MarketCatalystEvents with automated surprise evaluation.
2. Ingestion of NewsArticle wire headlines with SHA-256 deduplication and sentiment classification.
3. Automated entity linking generating NewsCommodityTag instances linking headlines to multiple commodities.
"""

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.commodities.models import CommodityMaster
from apps.metadata.models import UnitMaster
from apps.news_intel.models import (
    MarketCatalystEvent,
    NewsArticle,
    NewsCommodityTag,
    EventType,
    ImpactLevel,
    EventStatus,
    SurpriseDirection,
    SentimentLabel,
)
from apps.news_intel.providers.factory import get_news_provider
from apps.news_intel.services.entity_linker import CommodityEntityLinker
from apps.news_intel.services.sentiment_engine import LexiconSentimentEngine
from apps.news_intel.services.surprise_engine import CatalystSurpriseEngine


class Command(BaseCommand):
    help = "Ingest macroeconomic catalyst calendar and multi-product news articles with sentiment analysis."

    def add_arguments(self, parser):
        parser.add_arguments_called = True
        parser.add_argument(
            "--provider",
            type=str,
            default=None,
            help="Provider to use ('static', 'rss', or custom class path). Defaults to settings.NEWS_PROVIDER.",
        )
        parser.add_argument(
            "--type",
            type=str,
            choices=["all", "catalysts", "articles"],
            default="all",
            help="Type of data to ingest ('all', 'catalysts', 'articles').",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing catalysts and news articles before ingestion.",
        )

    def handle(self, *args, **options):
        provider_name = options.get("provider")
        ingest_type = options.get("type", "all")
        clear_existing = options.get("clear", False)

        if provider_name:
            from django.conf import settings
            settings.NEWS_PROVIDER = provider_name

        provider = get_news_provider()
        self.stdout.write(self.style.NOTICE(f"Using News Intelligence Provider: {provider.__class__.__name__}"))

        if clear_existing:
            self.stdout.write(self.style.WARNING("Clearing existing news intelligence records..."))
            NewsCommodityTag.objects.all().delete()
            NewsArticle.objects.all().delete()
            MarketCatalystEvent.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Existing records successfully wiped."))

        commodity_cache = {c.code.upper(): c for c in CommodityMaster.objects.all()}
        unit_cache = {u.code.upper(): u for u in UnitMaster.objects.all()}

        catalysts_created = 0
        catalysts_updated = 0
        articles_created = 0
        articles_updated = 0
        tags_created = 0

        entity_linker = CommodityEntityLinker()
        sentiment_engine = LexiconSentimentEngine()

        # Ingest Catalyst Events
        if ingest_type in ["all", "catalysts"]:
            self.stdout.write(self.style.NOTICE("Ingesting Market Catalyst Events..."))
            raw_catalysts = provider.get_catalyst_events()

            with transaction.atomic():
                for raw_cat in raw_catalysts:
                    # Resolve primary commodity
                    primary_com = None
                    if raw_cat.primary_commodity_code:
                        primary_com = commodity_cache.get(raw_cat.primary_commodity_code.upper())

                    # Resolve unit
                    unit_obj = None
                    if raw_cat.unit_symbol:
                        unit_obj = unit_cache.get(raw_cat.unit_symbol.upper())

                    # Evaluate surprise
                    surprise_mag = raw_cat.surprise_magnitude
                    surprise_dir = raw_cat.surprise_direction

                    if surprise_mag is None and raw_cat.actual_value is not None and raw_cat.consensus_expectation is not None:
                        calc_mag, calc_dir = CatalystSurpriseEngine.evaluate_surprise(
                            actual_value=raw_cat.actual_value,
                            consensus_expectation=raw_cat.consensus_expectation,
                            event_type=raw_cat.event_type,
                            event_name=raw_cat.name,
                        )
                        surprise_mag = calc_mag
                        surprise_dir = calc_dir

                    catalyst, created = MarketCatalystEvent.objects.update_or_create(
                        name=raw_cat.name,
                        scheduled_datetime_utc=raw_cat.scheduled_datetime_utc,
                        defaults={
                            "event_type": raw_cat.event_type,
                            "impact_level": raw_cat.impact_level,
                            "status": raw_cat.status,
                            "primary_commodity": primary_com,
                            "source_agency": raw_cat.source_agency,
                            "period_covered": raw_cat.period_covered,
                            "consensus_expectation": raw_cat.consensus_expectation,
                            "actual_value": raw_cat.actual_value,
                            "prior_value": raw_cat.prior_value,
                            "unit": unit_obj,
                            "surprise_magnitude": surprise_mag,
                            "surprise_direction": surprise_dir,
                            "notes": raw_cat.notes,
                        },
                    )

                    # Link affected commodities
                    affected_objs = []
                    for code in raw_cat.affected_commodity_codes:
                        com = commodity_cache.get(code.upper())
                        if com:
                            affected_objs.append(com)
                    if affected_objs:
                        catalyst.affected_commodities.set(affected_objs)

                    if created:
                        catalysts_created += 1
                    else:
                        catalysts_updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Market Catalyst Events Processed: {catalysts_created} created, {catalysts_updated} updated."
                )
            )

        # Ingest News Articles & Multi-Commodity Tags
        if ingest_type in ["all", "articles"]:
            self.stdout.write(self.style.NOTICE("Ingesting News Articles & Multi-Commodity Tags..."))
            raw_articles = provider.get_news_articles(limit=100)

            with transaction.atomic():
                for raw_art in raw_articles:
                    # Content deduplication hash
                    norm_key = f"{raw_art.title.strip()}:{raw_art.published_at_utc.isoformat()}"
                    content_hash = hashlib.sha256(norm_key.encode("utf-8")).hexdigest()

                    # Compute or refine overall sentiment
                    text_for_analysis = f"{raw_art.title}. {raw_art.summary}"
                    sentiment_res = sentiment_engine.score_text(text_for_analysis)

                    overall_score = raw_art.overall_sentiment_score if raw_art.overall_sentiment_score != Decimal("0.000") else sentiment_res.score
                    overall_label = raw_art.overall_sentiment_label if raw_art.overall_sentiment_label != "NEUTRAL" else sentiment_res.label
                    confidence = raw_art.confidence_score or sentiment_res.confidence

                    # Resolve primary commodity
                    primary_com = None
                    if raw_art.primary_commodity_code:
                        primary_com = commodity_cache.get(raw_art.primary_commodity_code.upper())

                    # Match catalyst event if provided
                    catalyst_event = None
                    if raw_art.catalyst_event_name:
                        catalyst_event = MarketCatalystEvent.objects.filter(
                            name__icontains=raw_art.catalyst_event_name
                        ).first()

                    article, art_created = NewsArticle.objects.update_or_create(
                        content_hash=content_hash,
                        defaults={
                            "title": raw_art.title,
                            "summary": raw_art.summary,
                            "content": raw_art.content,
                            "source_name": raw_art.source_name,
                            "source_url": raw_art.source_url,
                            "published_at_utc": raw_art.published_at_utc,
                            "author": raw_art.author,
                            "overall_sentiment_score": overall_score,
                            "overall_sentiment_label": overall_label,
                            "confidence_score": confidence,
                            "is_breaking": raw_art.is_breaking,
                            "primary_commodity": primary_com,
                            "catalyst_event": catalyst_event,
                        },
                    )

                    if art_created:
                        articles_created += 1
                    else:
                        articles_updated += 1

                    # Establish Multi-Commodity Tags
                    # If raw_art came with pre-configured tags, use them; otherwise, invoke CommodityEntityLinker
                    tags_to_apply = []
                    if raw_art.tags:
                        for tag_dto in raw_art.tags:
                            com = commodity_cache.get(tag_dto.commodity_code.upper())
                            if com:
                                tags_to_apply.append({
                                    "commodity": com,
                                    "relevance_score": tag_dto.relevance_score,
                                    "is_primary": tag_dto.is_primary,
                                    "commodity_sentiment": tag_dto.commodity_sentiment,
                                    "commodity_sentiment_score": tag_dto.commodity_sentiment_score,
                                    "matched_keywords": tag_dto.matched_keywords,
                                })
                    else:
                        # Automated entity linker
                        linked = entity_linker.link_entities(
                            text_for_analysis,
                            explicit_primary_code=raw_art.primary_commodity_code,
                        )
                        for matched in linked:
                            com = commodity_cache.get(matched.commodity_code.upper())
                            if com:
                                com_score, com_label = sentiment_engine.score_commodity_sentiment(
                                    overall_res=sentiment_res,
                                    commodity_code=matched.commodity_code,
                                    text=text_for_analysis,
                                    relevance_score=matched.relevance_score,
                                )
                                tags_to_apply.append({
                                    "commodity": com,
                                    "relevance_score": matched.relevance_score,
                                    "is_primary": matched.is_primary,
                                    "commodity_sentiment": com_label,
                                    "commodity_sentiment_score": com_score,
                                    "matched_keywords": matched.matched_keywords,
                                })

                    # Ensure article's primary_commodity is synced
                    for tag_info in tags_to_apply:
                        if tag_info["is_primary"] and article.primary_commodity is None:
                            article.primary_commodity = tag_info["commodity"]
                            article.save(update_fields=["primary_commodity"])

                        tag_obj, tag_created = NewsCommodityTag.objects.update_or_create(
                            article=article,
                            commodity=tag_info["commodity"],
                            defaults={
                                "relevance_score": tag_info["relevance_score"],
                                "is_primary": tag_info["is_primary"],
                                "commodity_sentiment": tag_info["commodity_sentiment"],
                                "commodity_sentiment_score": tag_info["commodity_sentiment_score"],
                                "matched_keywords": tag_info["matched_keywords"],
                            },
                        )
                        if tag_created:
                            tags_created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"News Articles Processed: {articles_created} created, {articles_updated} updated. "
                    f"Multi-Commodity Tags established: {tags_created}."
                )
            )
