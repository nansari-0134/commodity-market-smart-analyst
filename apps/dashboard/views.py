"""
Views for the Intelligence Terminal Dashboard.
"""
from django.shortcuts import render
from django.db import connection
from django.conf import settings
from django.utils import timezone


def index(request):
    """Renders the main Commodity Intelligence Terminal overview."""
    db_healthy = True
    db_vendor = connection.vendor
    try:
        connection.ensure_connection()
    except Exception:
        db_healthy = False

    from apps.metadata.models import DataDomainMaster, UnitMaster, FrequencyMaster
    from apps.exchanges.models import ExchangeMaster, ExchangeTradingSession, ExchangeHoliday
    from apps.commodities.models import CommodityMaster, CommodityExchangeListing
    from apps.contracts.models import ContractSpecification, ContractExpiry
    from apps.datasets.models import DatasetMaster

    phases = [
        {"id": "Phase 1", "name": "Django + PostgreSQL Foundation", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 2", "name": "Metadata Schema", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 3", "name": "Exchange Master", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 4", "name": "Commodity Master", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 5", "name": "Product / Instrument / Contract Master", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 6", "name": "Dataset Master", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 7", "name": "Variable Master", "status": "PENDING"},
        {"id": "Phase 8", "name": "Source / Provider Master", "status": "PENDING"},
        {"id": "Phase 9", "name": "Endpoint & API Metadata", "status": "PENDING"},
        {"id": "Phase 10", "name": "Data Contract", "status": "PENDING"},
    ]

    pipeline_stages = [
        {"num": "01", "name": "RAW DATA", "desc": "Provider plugins, immutable raw captures, source hashing"},
        {"num": "02", "name": "DATA INGESTION", "desc": "Failover priority, rate-limited adapters, schedulers"},
        {"num": "03", "name": "NORMALIZATION", "desc": "Canonical schema mapping, point-in-time timestamping"},
        {"num": "04", "name": "DATA QUALITY", "desc": "Deterministic rule engine (outliers, rolls, missingness)"},
        {"num": "05", "name": "QUANT ENGINE", "desc": "Futures curves, spreads, carrying charges, momentum"},
        {"num": "06", "name": "FUNDAMENTALS", "desc": "Supply/demand balances, trade flows, inventory regimes"},
        {"num": "07", "name": "NEWS & EVENTS", "desc": "Market surprises, expectation revisions, sentiment"},
        {"num": "08", "name": "KNOWLEDGE GRAPH", "desc": "Entity linkages, supply chains, cross-market flows"},
        {"num": "09", "name": "HYBRID RAG", "desc": "SQL features + Vector docs + Graph traversal"},
        {"num": "10", "name": "MARKET NARRATIVE", "desc": "LLM evidence-based reasoning, scenarios & trades"},
    ]

    domain_count = DataDomainMaster.objects.filter(is_active=True).count()
    unit_count = UnitMaster.objects.filter(is_active=True).count()
    freq_count = FrequencyMaster.objects.filter(is_active=True).count()
    exchange_count = ExchangeMaster.objects.filter(is_active=True).count()
    session_count = ExchangeTradingSession.objects.filter(is_active=True).count()
    holiday_count = ExchangeHoliday.objects.filter(is_active=True).count()
    commodity_count = CommodityMaster.objects.filter(is_active=True).count()
    listing_count = CommodityExchangeListing.objects.filter(is_active=True).count()
    contract_spec_count = ContractSpecification.objects.filter(is_active=True).count()
    contract_expiry_count = ContractExpiry.objects.filter(is_active=True).count()
    dataset_count = DatasetMaster.objects.filter(is_active=True).count()

    context = {
        "page_title": "Terminal Overview",
        "db_healthy": db_healthy,
        "db_vendor": db_vendor.upper(),
        "server_time": timezone.now(),
        "phases": phases,
        "pipeline_stages": pipeline_stages,
        "app_name": getattr(settings, "APP_NAME", "Commodity Market Intelligence"),
        "version": getattr(settings, "APP_VERSION", "0.1.0-alpha"),
        "domain_count": domain_count,
        "unit_count": unit_count,
        "freq_count": freq_count,
        "exchange_count": exchange_count,
        "session_count": session_count,
        "holiday_count": holiday_count,
        "commodity_count": commodity_count,
        "listing_count": listing_count,
        "contract_spec_count": contract_spec_count,
        "contract_expiry_count": contract_expiry_count,
        "dataset_count": dataset_count,
    }
    return render(request, "dashboard/index.html", context)
