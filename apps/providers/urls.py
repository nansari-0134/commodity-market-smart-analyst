"""
URL patterns for Provider Master REST API endpoints.
"""

from django.urls import path

from apps.providers.views import (
    ProviderDetailAPIView,
    ProviderListAPIView,
    ProviderSummaryAPIView,
)

app_name = "providers"

urlpatterns = [
    path("", ProviderListAPIView.as_view(), name="provider-list"),
    path("summary/", ProviderSummaryAPIView.as_view(), name="provider-summary"),
    path("<str:code_or_uuid>/", ProviderDetailAPIView.as_view(), name="provider-detail"),
]
