"""
URL Routing for Contract Master and Derivatives REST API.
"""

from django.urls import path
from apps.contracts.views import (
    ContractSpecificationListView,
    ContractSpecificationDetailView,
    ContractExpiryListView,
    ContractExpiryDetailView,
    ContractSummaryView,
)

app_name = "contracts"

urlpatterns = [
    path("specifications/", ContractSpecificationListView.as_view(), name="specification-list"),
    path("specifications/<str:lookup>/", ContractSpecificationDetailView.as_view(), name="specification-detail"),
    path("expiries/", ContractExpiryListView.as_view(), name="expiry-list"),
    path("expiries/<str:lookup>/", ContractExpiryDetailView.as_view(), name="expiry-detail"),
    path("summary/", ContractSummaryView.as_view(), name="summary"),
]
