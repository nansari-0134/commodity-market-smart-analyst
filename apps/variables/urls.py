"""
URL configuration for Variable Master catalog endpoints.
"""

from django.urls import path
from apps.variables.views import (
    VariableMasterDetailView,
    VariableMasterListView,
    VariableSummaryView,
)

app_name = "variables"

urlpatterns = [
    path("", VariableMasterListView.as_view(), name="variable_list"),
    path("summary/", VariableSummaryView.as_view(), name="variable_summary"),
    path("<str:lookup>/", VariableMasterDetailView.as_view(), name="variable_detail"),
]
