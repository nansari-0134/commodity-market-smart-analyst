"""
URL patterns for core infrastructure and health monitoring.
"""
from django.urls import path
from .views import health_check, SystemStatusAPIView

app_name = "core"

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("api/health/", SystemStatusAPIView.as_view(), name="api_health_check"),
]
