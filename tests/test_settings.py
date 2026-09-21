"""
Tests for platform configuration and settings adherence.
"""
from django.conf import settings


def test_settings_loaded():
    """Verify that Django settings are loaded properly."""
    assert settings.configured is True


def test_timezone_is_utc():
    """Verify UTC timezone enforcement for point-in-time quantitative accuracy."""
    assert settings.TIME_ZONE == "UTC"
    assert settings.USE_TZ is True


def test_installed_apps_contain_core_modules():
    """Verify that essential platform apps and third-party dependencies are installed."""
    assert "rest_framework" in settings.INSTALLED_APPS
    assert "apps.core.apps.CoreConfig" in settings.INSTALLED_APPS
    assert "apps.dashboard.apps.DashboardConfig" in settings.INSTALLED_APPS
    assert "apps.commodities.apps.CommoditiesConfig" in settings.INSTALLED_APPS
    assert "apps.contracts.apps.ContractsConfig" in settings.INSTALLED_APPS


def test_base_directory_structure():
    """Verify root base directory resolution."""
    assert settings.BASE_DIR.exists()
    assert (settings.BASE_DIR / "config").exists()
    assert (settings.BASE_DIR / "apps").exists()
