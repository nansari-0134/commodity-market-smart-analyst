"""
URL Routing for Commodity Master REST API.
"""
from django.urls import path
from apps.commodities.views import (
    CommodityListAPIView,
    CommodityDetailAPIView,
    CommodityListingsAPIView,
    CommoditySummaryAPIView,
    CommoditySectorsAPIView,
)

app_name = "commodities"

urlpatterns = [
    path("", CommodityListAPIView.as_view(), name="commodity_list"),
    path("summary/", CommoditySummaryAPIView.as_view(), name="commodity_summary"),
    path("sectors/", CommoditySectorsAPIView.as_view(), name="commodity_sectors"),
    path("<str:identifier>/", CommodityDetailAPIView.as_view(), name="commodity_detail"),
    path("<str:identifier>/listings/", CommodityListingsAPIView.as_view(), name="commodity_listings"),
]
