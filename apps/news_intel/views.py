"""
REST API Views and ViewSets for News Intelligence and Macroeconomic Catalyst Calendar.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from django.db.models import Avg, Count, Q
from django.utils.dateparse import parse_datetime, parse_date
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.commodities.models import CommodityMaster
from apps.news_intel.models import (
    MarketCatalystEvent,
    NewsArticle,
    NewsCommodityTag,
    SentimentLabel,
)
from apps.news_intel.serializers import (
    MarketCatalystEventSerializer,
    NewsArticleSerializer,
    NewsSentimentSummarySerializer,
)


class MarketCatalystEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for macroeconomic catalyst calendar releases.
    Supports filtering by commodity, event type, impact level, and date ranges.
    """
    queryset = MarketCatalystEvent.objects.select_related(
        "primary_commodity", "unit"
    ).prefetch_related("affected_commodities").all()
    serializer_class = MarketCatalystEventSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        commodity = params.get("commodity")
        if commodity:
            code = commodity.upper()
            qs = qs.filter(
                Q(primary_commodity__code=code) | Q(affected_commodities__code=code)
            ).distinct()

        event_type = params.get("event_type")
        if event_type:
            qs = qs.filter(event_type=event_type)

        impact_level = params.get("impact_level")
        if impact_level:
            qs = qs.filter(impact_level=impact_level)

        event_status = params.get("status")
        if event_status:
            qs = qs.filter(status=event_status)

        start_date = params.get("start_date")
        if start_date:
            parsed = parse_date(start_date)
            if parsed:
                qs = qs.filter(scheduled_datetime_utc__date__gte=parsed)

        end_date = params.get("end_date")
        if end_date:
            parsed = parse_date(end_date)
            if parsed:
                qs = qs.filter(scheduled_datetime_utc__date__lte=parsed)

        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(notes__icontains=search)
                | Q(source_agency__icontains=search)
            )

        return qs

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Return scheduled catalysts occurring within the next N days (default 14 days)."""
        days = int(request.query_params.get("days", 14))
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days)

        commodity = request.query_params.get("commodity")
        qs = self.get_queryset().filter(
            scheduled_datetime_utc__gte=now,
            scheduled_datetime_utc__lte=cutoff,
            status="SCHEDULED",
        ).order_by("scheduled_datetime_utc")

        if commodity:
            code = commodity.upper()
            qs = qs.filter(
                Q(primary_commodity__code=code) | Q(affected_commodities__code=code)
            ).distinct()

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class NewsArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for multi-product news articles and wire headlines.
    Enables filtering across multiple linked commodities with per-asset relevance and sentiment.
    """
    queryset = NewsArticle.objects.select_related(
        "primary_commodity", "catalyst_event"
    ).prefetch_related("commodity_tags__commodity").all()
    serializer_class = NewsArticleSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        commodity = params.get("commodity")
        if commodity:
            code = commodity.upper()
            qs = qs.filter(
                Q(primary_commodity__code=code) | Q(commodities__code=code)
            ).distinct()

        sentiment = params.get("sentiment")
        if sentiment:
            qs = qs.filter(overall_sentiment_label=sentiment)

        is_breaking = params.get("is_breaking")
        if is_breaking is not None:
            val = is_breaking.lower() in ["true", "1", "yes"]
            qs = qs.filter(is_breaking=val)

        source = params.get("source")
        if source:
            qs = qs.filter(source_name__icontains=source)

        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(summary__icontains=search)
                | Q(content__icontains=search)
            )

        return qs

    @action(detail=False, methods=["get"])
    def breaking(self, request):
        """Retrieve highest priority breaking news items."""
        qs = self.get_queryset().filter(is_breaking=True)[:10]
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class NewsSentimentSummaryView(APIView):
    """
    Aggregated market sentiment breakdown across commodities.
    Combines news article sentiment tags and upcoming macroeconomic catalysts.
    """

    def get(self, request):
        commodities = CommodityMaster.objects.filter(is_active=True)
        now = datetime.now(timezone.utc)
        upcoming_cutoff = now + timedelta(days=14)

        summary_results = []
        for com in commodities:
            tags = NewsCommodityTag.objects.filter(commodity=com).select_related("article")
            tag_count = tags.count()

            if tag_count == 0:
                continue

            avg_score = tags.aggregate(avg=Avg("commodity_sentiment_score"))["avg"] or Decimal("0.000")
            float_score = float(avg_score)

            bullish_count = tags.filter(commodity_sentiment__in=["STRONG_BULLISH", "MODERATE_BULLISH"]).count()
            bearish_count = tags.filter(commodity_sentiment__in=["STRONG_BEARISH", "MODERATE_BEARISH"]).count()
            neutral_count = tags.filter(commodity_sentiment="NEUTRAL").count()

            if float_score >= 0.45:
                dominant_label = "STRONG_BULLISH"
            elif float_score >= 0.15:
                dominant_label = "MODERATE_BULLISH"
            elif float_score <= -0.45:
                dominant_label = "STRONG_BEARISH"
            elif float_score <= -0.15:
                dominant_label = "MODERATE_BEARISH"
            else:
                dominant_label = "NEUTRAL"

            upcoming_catalysts = MarketCatalystEvent.objects.filter(
                Q(primary_commodity=com) | Q(affected_commodities=com),
                scheduled_datetime_utc__gte=now,
                scheduled_datetime_utc__lte=upcoming_cutoff,
                status="SCHEDULED",
            ).distinct().count()

            summary_results.append({
                "commodity_code": com.code,
                "commodity_name": com.name,
                "article_count": tag_count,
                "average_sentiment_score": round(float_score, 3),
                "dominant_sentiment_label": dominant_label,
                "bullish_count": bullish_count,
                "bearish_count": bearish_count,
                "neutral_count": neutral_count,
                "upcoming_catalysts_count": upcoming_catalysts,
            })

        summary_results.sort(key=lambda x: x["article_count"], reverse=True)
        serializer = NewsSentimentSummarySerializer(summary_results, many=True)
        return Response(serializer.data)
