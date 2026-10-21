"""
URL Routing for Narratives API endpoints.
"""
from django.urls import path
from .views import (
    MarketNarrativeListView,
    MarketNarrativeDetailView,
    LatestMarketNarrativeView,
    GenerateMarketNarrativeView,
    NarrativesSummaryView,
)

app_name = "narratives"

urlpatterns = [
    path("narratives/", MarketNarrativeListView.as_view(), name="narrative-list"),
    path("narratives/latest/", LatestMarketNarrativeView.as_view(), name="narrative-latest"),
    path("narratives/generate/", GenerateMarketNarrativeView.as_view(), name="narrative-generate"),
    path("narratives/summary/", NarrativesSummaryView.as_view(), name="narrative-summary"),
    path("narratives/<uuid:id>/", MarketNarrativeDetailView.as_view(), name="narrative-detail"),
]
