"""
Serializers for News & Macroeconomic Catalyst Intelligence REST APIs.
"""

from rest_framework import serializers
from apps.news_intel.models import MarketCatalystEvent, NewsArticle, NewsCommodityTag


class NewsCommodityTagSerializer(serializers.ModelSerializer):
    """Serializer for individual commodity tags linked to a news article."""
    commodity_code = serializers.CharField(source="commodity.code", read_only=True)
    commodity_name = serializers.CharField(source="commodity.name", read_only=True)
    commodity_sector = serializers.CharField(source="commodity.sector", read_only=True)

    class Meta:
        model = NewsCommodityTag
        fields = [
            "commodity_code",
            "commodity_name",
            "commodity_sector",
            "relevance_score",
            "is_primary",
            "commodity_sentiment",
            "commodity_sentiment_score",
            "matched_keywords",
        ]


class MarketCatalystEventSerializer(serializers.ModelSerializer):
    """Serializer for scheduled and historical macroeconomic catalyst events."""
    primary_commodity_code = serializers.CharField(source="primary_commodity.code", read_only=True, allow_null=True)
    primary_commodity_name = serializers.CharField(source="primary_commodity.name", read_only=True, allow_null=True)
    unit_symbol = serializers.CharField(source="unit.symbol", read_only=True, allow_null=True)
    affected_commodities = serializers.SerializerMethodField()

    class Meta:
        model = MarketCatalystEvent
        fields = [
            "id",
            "name",
            "event_type",
            "impact_level",
            "scheduled_datetime_utc",
            "status",
            "source_agency",
            "period_covered",
            "primary_commodity_code",
            "primary_commodity_name",
            "affected_commodities",
            "consensus_expectation",
            "actual_value",
            "prior_value",
            "unit_symbol",
            "surprise_magnitude",
            "surprise_direction",
            "notes",
            "created_at",
            "updated_at",
        ]

    def get_affected_commodities(self, obj):
        return [
            {
                "code": c.code,
                "name": c.name,
                "sector": c.sector,
            }
            for c in obj.affected_commodities.all()
        ]


class NewsArticleSerializer(serializers.ModelSerializer):
    """Serializer for standardized multi-product news articles."""
    primary_commodity_code = serializers.CharField(source="primary_commodity.code", read_only=True, allow_null=True)
    primary_commodity_name = serializers.CharField(source="primary_commodity.name", read_only=True, allow_null=True)
    catalyst_event_name = serializers.CharField(source="catalyst_event.name", read_only=True, allow_null=True)
    commodity_tags = NewsCommodityTagSerializer(many=True, read_only=True)

    class Meta:
        model = NewsArticle
        fields = [
            "id",
            "title",
            "summary",
            "content",
            "source_name",
            "source_url",
            "published_at_utc",
            "author",
            "content_hash",
            "overall_sentiment_score",
            "overall_sentiment_label",
            "confidence_score",
            "is_breaking",
            "primary_commodity_code",
            "primary_commodity_name",
            "catalyst_event_name",
            "commodity_tags",
            "created_at",
            "updated_at",
        ]


class NewsSentimentSummarySerializer(serializers.Serializer):
    """Aggregated sentiment breakdown across commodities."""
    commodity_code = serializers.CharField()
    commodity_name = serializers.CharField()
    article_count = serializers.IntegerField()
    average_sentiment_score = serializers.FloatField()
    dominant_sentiment_label = serializers.CharField()
    bullish_count = serializers.IntegerField()
    bearish_count = serializers.IntegerField()
    neutral_count = serializers.IntegerField()
    upcoming_catalysts_count = serializers.IntegerField()
