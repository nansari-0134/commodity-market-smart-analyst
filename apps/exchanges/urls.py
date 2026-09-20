"""
URL patterns for Exchange Master and trading calendar endpoints.
"""
from django.urls import path
from .views import (
    ExchangeListAPIView,
    ExchangeDetailAPIView,
    ExchangeTradingDayAPIView,
    ExchangeHolidayListAPIView,
    ExchangeSummaryAPIView,
)

app_name = "exchanges"

urlpatterns = [
    path("", ExchangeListAPIView.as_view(), name="exchange_list"),
    path("summary/", ExchangeSummaryAPIView.as_view(), name="exchange_summary"),
    path("<str:identifier>/", ExchangeDetailAPIView.as_view(), name="exchange_detail"),
    path("<str:identifier>/is-trading-day/", ExchangeTradingDayAPIView.as_view(), name="is_trading_day"),
    path("<str:identifier>/holidays/", ExchangeHolidayListAPIView.as_view(), name="exchange_holidays"),
]
