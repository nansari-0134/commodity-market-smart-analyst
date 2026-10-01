"""
URL routing configuration for News Intelligence and Catalyst Calendar APIs.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MarketCatalystEventViewSet,
    NewsArticleViewSet,
    NewsSentimentSummaryView,
)

router = DefaultRouter()
router.register(r"catalysts", MarketCatalystEventViewSet, basename="catalyst-events")
router.register(r"articles", NewsArticleViewSet, basename="news-articles")

urlpatterns = [
    path("", include(router.urls)),
    path("summary/", NewsSentimentSummaryView.as_view(), name="news-sentiment-summary"),
]
