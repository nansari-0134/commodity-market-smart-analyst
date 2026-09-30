"""
REST API URL routing for Quantitative Engine.
"""
from django.urls import path
from apps.quant_engine.views import (
    QuantitativeEvidencePackageView,
    MarketStateView,
    ForwardCurveView,
    SpreadsView,
    CrossCommodityView,
    SeasonalityView,
    DiscoveryRegistryListView,
)

app_name = "quant_engine"

urlpatterns = [
    path("evidence-package/", QuantitativeEvidencePackageView.as_view(), name="evidence-package"),
    path("market-state/", MarketStateView.as_view(), name="market-state"),
    path("curve/", ForwardCurveView.as_view(), name="curve"),
    path("spreads/", SpreadsView.as_view(), name="spreads"),
    path("cross-commodity/", CrossCommodityView.as_view(), name="cross-commodity"),
    path("seasonality/", SeasonalityView.as_view(), name="seasonality"),
    path("discoveries/", DiscoveryRegistryListView.as_view(), name="discoveries-list"),
]
