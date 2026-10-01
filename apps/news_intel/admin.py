"""
Django Admin interface configuration for News Intelligence and Market Catalysts.
"""

from django.contrib import admin
from apps.news_intel.models import MarketCatalystEvent, NewsArticle, NewsCommodityTag


class NewsCommodityTagInline(admin.TabularInline):
    """Inline editing of multi-commodity linkages on NewsArticle."""
    model = NewsCommodityTag
    extra = 1
    autocomplete_fields = ["commodity"]
    fields = [
        "commodity",
        "relevance_score",
        "is_primary",
        "commodity_sentiment",
        "commodity_sentiment_score",
        "matched_keywords",
    ]


@admin.register(MarketCatalystEvent)
class MarketCatalystEventAdmin(admin.ModelAdmin):
    """Admin configuration for scheduled and historic macroeconomic catalysts."""
    list_display = [
        "name",
        "event_type",
        "impact_level",
        "status",
        "primary_commodity",
        "scheduled_datetime_utc",
        "consensus_expectation",
        "actual_value",
        "surprise_magnitude",
        "surprise_direction",
    ]
    list_filter = [
        "event_type",
        "impact_level",
        "status",
        "surprise_direction",
        "primary_commodity",
    ]
    search_fields = ["name", "source_agency", "notes"]
    filter_horizontal = ["affected_commodities"]
    date_hierarchy = "scheduled_datetime_utc"
    ordering = ["-scheduled_datetime_utc"]


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    """Admin configuration for news headlines and articles."""
    list_display = [
        "title",
        "primary_commodity",
        "overall_sentiment_label",
        "overall_sentiment_score",
        "source_name",
        "is_breaking",
        "published_at_utc",
    ]
    list_filter = [
        "overall_sentiment_label",
        "is_breaking",
        "source_name",
        "primary_commodity",
    ]
    search_fields = ["title", "summary", "content", "source_name"]
    date_hierarchy = "published_at_utc"
    ordering = ["-published_at_utc"]
    inlines = [NewsCommodityTagInline]


@admin.register(NewsCommodityTag)
class NewsCommodityTagAdmin(admin.ModelAdmin):
    """Admin configuration for granular news-commodity tag links."""
    list_display = [
        "article",
        "commodity",
        "relevance_score",
        "is_primary",
        "commodity_sentiment",
        "commodity_sentiment_score",
    ]
    list_filter = ["commodity", "commodity_sentiment", "is_primary"]
    search_fields = ["article__title", "commodity__code", "commodity__name"]
