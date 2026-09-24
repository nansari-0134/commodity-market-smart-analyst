"""
URL Configuration for apps.market_data REST API.
"""

from django.urls import path

from apps.market_data.views import (
    MarketPriceListAPIView,
    MarketPriceDetailAPIView,
    FundamentalObservationListAPIView,
    FundamentalObservationDetailAPIView,
    CommitmentOfTradersListAPIView,
    CommitmentOfTradersDetailAPIView,
    MarketDataSummaryAPIView,
)

app_name = "market_data"

urlpatterns = [
    # Prices
    path("prices/", MarketPriceListAPIView.as_view(), name="price-list"),
    path("prices/<uuid:pk>/", MarketPriceDetailAPIView.as_view(), name="price-detail"),
    # Fundamentals
    path("fundamentals/", FundamentalObservationListAPIView.as_view(), name="fundamental-list"),
    path("fundamentals/<uuid:pk>/", FundamentalObservationDetailAPIView.as_view(), name="fundamental-detail"),
    # COT Positioning
    path("cot/", CommitmentOfTradersListAPIView.as_view(), name="cot-list"),
    path("cot/<uuid:pk>/", CommitmentOfTradersDetailAPIView.as_view(), name="cot-detail"),
    # Telemetry Summary
    path("summary/", MarketDataSummaryAPIView.as_view(), name="market-data-summary"),
]
