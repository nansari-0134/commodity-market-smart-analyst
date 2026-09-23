"""
URL routing for the dashboard application.
"""
from django.urls import path
from .views import index, explorer

app_name = "dashboard"

urlpatterns = [
    path("", index, name="index"),
    path("explorer/", explorer, name="explorer"),
]
