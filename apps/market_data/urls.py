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
    CommitmentOfTradersAnalyticsAPIView,
    OptionsObservationListAPIView,
    ForwardCurveAnalyticsAPIView,
    SpreadAnalyticsAPIView,
    MarketDataSummaryAPIView,
    LiveMarketQuoteAPIView,
)

app_name = "market_data"

urlpatterns = [
    # Live Real-Time & Streaming Intraday Quotes
    path("live-quote/", LiveMarketQuoteAPIView.as_view(), name="live-quote"),
    # Prices
    path("prices/", MarketPriceListAPIView.as_view(), name="price-list"),
    path("prices/<uuid:pk>/", MarketPriceDetailAPIView.as_view(), name="price-detail"),
    # Forward Curve & Options Surfaces (M1-M24)
    path("forward-curve/analytics/", ForwardCurveAnalyticsAPIView.as_view(), name="forward-curve-analytics"),
    path("options/", OptionsObservationListAPIView.as_view(), name="options-list"),
    # Cross-Commodity & Processing Spreads
    path("spreads/analytics/", SpreadAnalyticsAPIView.as_view(), name="spreads-analytics"),
    # Fundamentals
    path("fundamentals/", FundamentalObservationListAPIView.as_view(), name="fundamental-list"),
    path("fundamentals/<uuid:pk>/", FundamentalObservationDetailAPIView.as_view(), name="fundamental-detail"),
    # COT Positioning & Seasonality Engine
    path("cot/", CommitmentOfTradersListAPIView.as_view(), name="cot-list"),
    path("cot/analytics/", CommitmentOfTradersAnalyticsAPIView.as_view(), name="cot-analytics"),
    path("cot/<uuid:pk>/", CommitmentOfTradersDetailAPIView.as_view(), name="cot-detail"),
    # Telemetry Summary
    path("summary/", MarketDataSummaryAPIView.as_view(), name="market-data-summary"),
]
