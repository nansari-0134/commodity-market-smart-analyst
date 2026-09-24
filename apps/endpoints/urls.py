"""
URL patterns for Endpoint Master REST API endpoints.
"""

from django.urls import path

from apps.endpoints.views import (
    EndpointDetailAPIView,
    EndpointListAPIView,
    EndpointSummaryAPIView,
)

app_name = "endpoints"

urlpatterns = [
    path("", EndpointListAPIView.as_view(), name="endpoint-list"),
    path("summary/", EndpointSummaryAPIView.as_view(), name="endpoint-summary"),
    path("<str:code_or_uuid>/", EndpointDetailAPIView.as_view(), name="endpoint-detail"),
]
