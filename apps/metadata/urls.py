"""
URL routing for metadata catalog endpoints.
"""
from django.urls import path
from .views import (
    DataDomainListAPIView,
    UnitListAPIView,
    FrequencyListAPIView,
    MetadataSummaryAPIView,
)

app_name = "metadata"

urlpatterns = [
    path("domains/", DataDomainListAPIView.as_view(), name="domain_list"),
    path("units/", UnitListAPIView.as_view(), name="unit_list"),
    path("frequencies/", FrequencyListAPIView.as_view(), name="frequency_list"),
    path("summary/", MetadataSummaryAPIView.as_view(), name="metadata_summary"),
]
