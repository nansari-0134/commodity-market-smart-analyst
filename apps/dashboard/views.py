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

    phases = [
        {"id": "Phase 1", "name": "Django + PostgreSQL Foundation", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 2", "name": "Metadata Schema", "status": "PENDING"},
        {"id": "Phase 3", "name": "Exchange Master", "status": "PENDING"},
        {"id": "Phase 4", "name": "Commodity Master", "status": "PENDING"},
        {"id": "Phase 5", "name": "Product / Instrument / Contract Master", "status": "PENDING"},
        {"id": "Phase 6", "name": "Dataset Master", "status": "PENDING"},
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

    context = {
        "page_title": "Terminal Overview",
        "db_healthy": db_healthy,
        "db_vendor": db_vendor.upper(),
        "server_time": timezone.now(),
        "phases": phases,
        "pipeline_stages": pipeline_stages,
        "app_name": getattr(settings, "APP_NAME", "Commodity Market Intelligence"),
        "version": getattr(settings, "APP_VERSION", "0.1.0-alpha"),
    }
    return render(request, "dashboard/index.html", context)
