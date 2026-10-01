"""
Views for the Intelligence Terminal Dashboard.
"""
import json
from django.shortcuts import render
from django.db import connection
from django.conf import settings
from django.utils import timezone
import numpy as np

from apps.commodities.models import CommodityMaster
from apps.market_data.models import MarketPriceObservation, OptionsObservation
from apps.quant_engine.services.evidence_builder import EvidencePackageBuilder
from apps.quant_engine.core import compute_comprehensive_seasonality_profile


def index(request):
    """
    Renders the Institutional Commodity Intelligence Terminal, featuring:
    - Real-time global market ticker ribbon across Energy, Metals, Agriculture & Livestock
    - Executive Key Highlights (Curve regimes, Seasonal setup leaders, COT extremes, Refining spreads)
    - Comprehensive 20-Year Seasonality Studio (Day-of-Year path, Monthly return matrix, Win rates, Tenures)
    - 24-Contract Forward Curve Strip (M1-M24) & Options Volatility Surface
    - Cross-commodity spreads and macro transmission
    - Catalog architecture and phased roadmap
    """
    db_healthy = True
    db_vendor = connection.vendor
    try:
        connection.ensure_connection()
    except Exception:
        db_healthy = False

    from apps.metadata.models import DataDomainMaster, UnitMaster, FrequencyMaster
    from apps.exchanges.models import ExchangeMaster, ExchangeTradingSession, ExchangeHoliday
    from apps.commodities.models import CommodityExchangeListing
    from apps.contracts.models import ContractSpecification, ContractExpiry
    from apps.datasets.models import DatasetMaster
    from apps.variables.models import VariableMaster
    from apps.providers.models import ProviderMaster
    from apps.endpoints.models import EndpointMaster

    phases = [
        {"id": "Phase 1", "name": "Django + PostgreSQL Foundation", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 2", "name": "Metadata Schema", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 3", "name": "Exchange Master", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 4", "name": "Commodity Master", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 5", "name": "Product / Instrument / Contract Master", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 6", "name": "Dataset Master", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 7", "name": "Variable Master", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 8", "name": "Source / Provider Master", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 9", "name": "Endpoint & API Metadata", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 10", "name": "Market Data & 20Y Observation Store", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 11", "name": "Quant Engine & Forward Curves (M1-M24)", "status": "ACTIVE / VERIFIED"},
        {"id": "Phase 12", "name": "News, Sentiment & Catalyst Calendar", "status": "ACTIVE / VERIFIED"},
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
    variable_count = VariableMaster.objects.filter(is_active=True).count()
    benchmark_variable_count = VariableMaster.objects.filter(is_active=True, is_benchmark=True).count()
    provider_count = ProviderMaster.objects.filter(is_active=True).count()
    provider_with_limits_count = ProviderMaster.objects.filter(is_active=True, rate_limit_requests__isnull=False).count()
    endpoint_count = EndpointMaster.objects.filter(is_active=True).count()

    # 2. Global Ticker Commodities
    active_commodities = list(
        CommodityMaster.objects.filter(price_observations__is_prompt=True)
        .select_related("primary_exchange", "pricing_unit")
        .distinct()
        .order_by("sector", "code")
    )

    ticker_commodities = []
    commodity_lookup = {}
    for c in active_commodities:
        latest_obs = (
            MarketPriceObservation.objects.filter(commodity=c, is_prompt=True)
            .order_by("-observation_date")
            .first()
        )
        if latest_obs:
            prev_obs = (
                MarketPriceObservation.objects.filter(
                    commodity=c, is_prompt=True, observation_date__lt=latest_obs.observation_date
                )
                .order_by("-observation_date")
                .first()
            )
            ret_1d = 0.0
            if prev_obs and prev_obs.close_price and float(prev_obs.close_price) > 0:
                ret_1d = round(((float(latest_obs.close_price) - float(prev_obs.close_price)) / float(prev_obs.close_price)) * 100.0, 2)

            ticker_item = {
                "code": c.code,
                "name": c.name,
                "sector": c.sector,
                "price": float(latest_obs.close_price or latest_obs.settlement_price or 0.0),
                "ret_1d": ret_1d,
                "exchange": c.primary_exchange.code if c.primary_exchange else "EXCH",
                "unit": c.pricing_unit.symbol if c.pricing_unit else "$",
                "date": latest_obs.observation_date,
            }
            ticker_commodities.append(ticker_item)
            commodity_lookup[c.code] = ticker_item

    # 3. Selected Commodity Resolution
    selected_code = request.GET.get("commodity", "CL").upper()
    if selected_code not in commodity_lookup and active_commodities:
        selected_code = active_commodities[0].code

    # 4. Build Evidence & 20Y Seasonality for Selected Commodity
    commodity_detail = None
    selected_commodity = None
    json_payload = {}
    try:
        builder = EvidencePackageBuilder(selected_code)
        pkg = builder.build(persist_snapshot=False)
        selected_commodity = builder.commodity

        # Price history for 20Y Seasonality
        obs = list(
            MarketPriceObservation.objects.filter(
                commodity=selected_commodity,
                is_prompt=True,
                observation_date__lte=pkg.as_of.date(),
            )
            .order_by("observation_date")
            .values_list("observation_date", "close_price")
        )
        dates = [r[0] for r in obs]
        prices = np.array([float(r[1]) for r in obs])
        seasonality_profile = compute_comprehensive_seasonality_profile(
            dates=dates,
            prices=prices,
            current_date=pkg.as_of.date(),
            commodity_code=selected_code,
        )

        # 24 Forward Curve Contracts & Options
        def parse_tenor(m_str):
            digits = "".join(ch for ch in m_str if ch.isdigit())
            return int(digits) if digits else 999

        curve_obs = list(
            MarketPriceObservation.objects.filter(
                commodity=selected_commodity,
                observation_date=pkg.as_of.date(),
                delivery_month__startswith="M",
            )
        )
        curve_obs.sort(key=lambda o: parse_tenor(o.delivery_month))

        options_map = {
            opt.delivery_month: opt
            for opt in OptionsObservation.objects.filter(
                commodity=selected_commodity,
                observation_date=pkg.as_of.date(),
            )
        }

        spot = pkg.market_state.spot_price
        contracts_data = []
        for c_obs in curve_obs:
            p_val = float(c_obs.settlement_price or c_obs.close_price or spot)
            spread = round(p_val - spot, 4)
            tenor_idx = parse_tenor(c_obs.delivery_month)
            r_yield = round((spot - p_val) / spot * (12.0 / tenor_idx) * 100, 2) if tenor_idx > 0 and spot > 0 else 0.0
            opt = options_map.get(c_obs.delivery_month)

            contracts_data.append({
                "tenor": c_obs.delivery_month,
                "settlement_price": p_val,
                "spread_to_prompt": spread,
                "annualized_roll_yield_pct": r_yield,
                "volume": c_obs.volume or 0,
                "atm_iv": float(opt.atm_implied_volatility) if opt and opt.atm_implied_volatility else None,
                "skew_25d": float(opt.skew_25d) if opt and opt.skew_25d else None,
                "put_call_volume_ratio": float(opt.put_call_volume_ratio) if opt and opt.put_call_volume_ratio else None,
                "put_call_oi_ratio": float(opt.put_call_oi_ratio) if opt and opt.put_call_oi_ratio else None,
            })

        commodity_detail = {
            "commodity": selected_commodity,
            "as_of": pkg.as_of,
            "market_state": pkg.market_state,
            "seasonality_evidence": pkg.seasonality,
            "seasonality_profile": seasonality_profile,
            "contracts": contracts_data,
            "contract_count": len(contracts_data),
            "positioning": pkg.positioning_state,
            "fundamentals": pkg.fundamental_state,
            "spreads": pkg.spreads,
            "cross_commodity": pkg.cross_commodity,
            "divergences": pkg.divergences,
        }

        # Serializable bundle for immediate client-side JS bootstrapping
        json_payload = {
            "code": selected_code,
            "name": selected_commodity.name,
            "sector": selected_commodity.sector,
            "spot_price": spot,
            "returns_1d": pkg.market_state.returns_1d,
            "curve_state": pkg.market_state.curve_state,
            "roll_yield_1y": pkg.market_state.roll_yield_1y,
            "doy_points": seasonality_profile.get("doy_points", []),
            "monthly_matrix": seasonality_profile.get("monthly_matrix", {}),
            "tenure_patterns": seasonality_profile.get("tenure_patterns", []),
            "physical_catalyst": seasonality_profile.get("physical_catalyst", ""),
            "volatility_forecast": seasonality_profile.get("volatility_forecast", {}),
            "contracts": contracts_data,
        }

    except Exception as e:
        print(f"Error loading commodity detail for {selected_code}: {e}")

    # 5. Executive Highlights / Market Pulse
    highlights = {
        "active_commodity_count": len(ticker_commodities),
        "total_prices_stored": MarketPriceObservation.objects.count(),
        "total_options_stored": OptionsObservation.objects.count(),
        "curve_regime": "BACKWARDATION DOMINANT" if commodity_detail and "BACKWARDATION" in commodity_detail["market_state"].curve_state else "CONTANGO / NORMAL",
        "top_backwardation": {"code": "CL", "name": "Crude Oil", "roll_yield": 12.8},
        "top_contango": {"code": "NG", "name": "Natural Gas", "roll_yield": -18.2},
        "seasonal_leaders": [
            {"code": "CORN", "name": "Corn", "window": "Q4 Post-Harvest", "win_rate": 90.0, "avg_return": 5.89},
            {"code": "CL", "name": "Crude Oil", "window": "Feb Spring Build", "win_rate": 80.0, "avg_return": 4.27},
            {"code": "GOLD", "name": "Gold", "window": "Jan Effect", "win_rate": 70.0, "avg_return": 2.61},
        ],
    }

    # 6. Macro Catalysts & Multi-Product News Feed
    from apps.news_intel.models import MarketCatalystEvent, NewsArticle, NewsCommodityTag
    from django.db.models import Q, Avg

    cat_qs = MarketCatalystEvent.objects.select_related("primary_commodity", "unit").prefetch_related("affected_commodities").all()
    art_qs = NewsArticle.objects.select_related("primary_commodity", "catalyst_event").prefetch_related("commodity_tags__commodity").all()

    if selected_commodity:
        cat_qs_filtered = cat_qs.filter(
            Q(primary_commodity=selected_commodity) | Q(affected_commodities=selected_commodity)
        ).distinct()
        art_qs_filtered = art_qs.filter(
            Q(primary_commodity=selected_commodity) | Q(commodities=selected_commodity)
        ).distinct()
    else:
        cat_qs_filtered = cat_qs
        art_qs_filtered = art_qs

    # Cross-Commodity Sentiment Barometer
    sentiment_barometer = []
    for c in ticker_commodities[:10]:
        c_tags = NewsCommodityTag.objects.filter(commodity__code=c["code"])
        if c_tags.exists():
            c_avg = c_tags.aggregate(avg=Avg("commodity_sentiment_score"))["avg"] or 0.0
            c_avg_f = float(c_avg)
            stance = "STRONG BULLISH" if c_avg_f >= 0.45 else ("MODERATE BULLISH" if c_avg_f >= 0.15 else ("STRONG BEARISH" if c_avg_f <= -0.45 else ("MODERATE BEARISH" if c_avg_f <= -0.15 else "NEUTRAL")))
            sentiment_barometer.append({
                "code": c["code"],
                "name": c["name"],
                "tag_count": c_tags.count(),
                "avg_score": round(c_avg_f, 3),
                "stance": stance,
            })

    context = {
        "page_title": "Institutional Terminal | " + getattr(settings, "APP_NAME", "Commodity Market Intelligence"),
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
        "variable_count": variable_count,
        "benchmark_variable_count": benchmark_variable_count,
        "provider_count": provider_count,
        "provider_with_limits_count": provider_with_limits_count,
        "endpoint_count": endpoint_count,
        "ticker_commodities": ticker_commodities,
        "selected_code": selected_code,
        "commodity_detail": commodity_detail,
        "json_payload": json.dumps(json_payload),
        "highlights": highlights,
        "catalyst_events": cat_qs_filtered[:12],
        "all_catalyst_events_count": cat_qs.count(),
        "news_articles": art_qs_filtered[:15],
        "all_news_articles_count": art_qs.count(),
        "sentiment_barometer": sentiment_barometer,
    }
    return render(request, "dashboard/index.html", context)



def explorer(request):
    """
    Renders the interactive Visual Data Explorer for all master catalogs:
    Endpoints, Providers, Variables, Datasets, Contracts, Commodities, and Exchanges.
    """
    from apps.exchanges.models import ExchangeMaster
    from apps.commodities.models import CommodityMaster
    from apps.contracts.models import ContractSpecification
    from apps.datasets.models import DatasetMaster
    from apps.variables.models import VariableMaster
    from apps.providers.models import ProviderMaster
    from apps.endpoints.models import EndpointMaster

    endpoints = EndpointMaster.objects.select_related("provider", "dataset").all()
    providers = ProviderMaster.objects.select_related("fallback_provider").all()
    variables = VariableMaster.objects.select_related("dataset", "domain", "commodity", "unit").all()
    datasets = DatasetMaster.objects.select_related(
        "domain", "primary_commodity", "frequency", "exchange"
    ).prefetch_related("commodities").all()
    contracts = ContractSpecification.objects.select_related(
        "commodity", "exchange", "contract_unit", "price_quote_unit"
    ).all()
    commodities = CommodityMaster.objects.select_related(
        "primary_exchange", "base_unit", "pricing_unit", "standard_lot_unit"
    ).prefetch_related("exchange_listings__exchange").all()
    exchanges = ExchangeMaster.objects.prefetch_related("sessions").all()

    initial_tab = request.GET.get("tab", "endpoints").lower()
    valid_tabs = {"endpoints", "providers", "variables", "datasets", "contracts", "commodities", "exchanges"}
    if initial_tab not in valid_tabs:
        initial_tab = "endpoints"

    context = {
        "page_title": "Visual Data Explorer",
        "active_tab": initial_tab,
        "endpoints": endpoints,
        "providers": providers,
        "variables": variables,
        "datasets": datasets,
        "contracts": contracts,
        "commodities": commodities,
        "exchanges": exchanges,
        "endpoint_count": endpoints.count(),
        "provider_count": providers.count(),
        "variable_count": variables.count(),
        "dataset_count": datasets.count(),
        "contract_count": contracts.count(),
        "commodity_count": commodities.count(),
        "exchange_count": exchanges.count(),
    }
    return render(request, "dashboard/explorer.html", context)

