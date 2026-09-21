"""
URL Routing for Dataset Master REST API.
"""

from django.urls import path
from apps.datasets.views import (
    DatasetMasterListView,
    DatasetMasterDetailView,
    DatasetSummaryView,
)

app_name = "datasets"

urlpatterns = [
    path("", DatasetMasterListView.as_view(), name="dataset-list"),
    path("summary/", DatasetSummaryView.as_view(), name="dataset-summary"),
    path("<str:lookup>/", DatasetMasterDetailView.as_view(), name="dataset-detail"),
]
