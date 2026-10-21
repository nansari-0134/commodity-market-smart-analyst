"""
Hybrid Context Builder Service.

Aggregates multi-source verified evidence across:
- apps/quant_engine (QuantitativeEvidencePackage, forward curves, seasonality, live features)
- apps/market_data (Fundamentals, CFTC COT positioning)
- apps/news_intel (Upcoming catalyst events, news headlines, and sentiment polarity)

Produces deterministic, hallucination-free prompt packages and evidence snapshots.
"""
import logging
from typing import Any, Dict, List, Tuple
from django.utils import timezone

from apps.commodities.models import CommodityMaster
from apps.quant_engine.services.evidence_builder import EvidencePackageBuilder
from apps.quant_engine.features.pipeline import FeaturePipeline
from apps.quant_engine.features.llm_formatter import format_llm_prompt_context
from apps.news_intel.models import MarketCatalystEvent, EventStatus, NewsCommodityTag

logger = logging.getLogger(__name__)


def build_narrative_context(commodity_code: str = "CL") -> Tuple[str, Dict[str, Any]]:
    """
    Builds structured Markdown prompt context and normalized context dictionary.
    
    Returns:
        Tuple of (prompt_markdown: str, context_dict: Dict[str, Any])
    """
    symbol = (commodity_code or "CL").upper().strip()
    commodity = CommodityMaster.objects.filter(code=symbol).first()
    commodity_name = commodity.name if commodity else f"Commodity ({symbol})"
    sector = commodity.sector if commodity else "Energy"

    context_dict: Dict[str, Any] = {
        "commodity_code": symbol,
        "commodity_name": commodity_name,
        "sector": sector,
        "as_of": timezone.now().isoformat(),
        "last_price": 0.0,
        "return_1d": 0.0,
        "regime": "NEUTRAL",
        "trend": "rangebound",
        "vol_regime": "normal",
        "curve_state": "FLAT",
        "spread_f1_f2": 0.0,
        "adx": 20.0,
        "rsi": 50.0,
        "rvol": 1.0,
        "composite_score": 0.0,
        "divergences": [],
        "fundamentals": {},
        "cot_positioning": {},
        "seasonality_tendency": {},
        "upcoming_catalysts": [],
        "recent_news": [],
        "sentiment_score": 0.0,
    }

    markdown_sections: List[str] = [
        f"# GROUND-TRUTH MARKET EVIDENCE: {commodity_name} [{symbol}]",
        f"**Sector**: {sector} | **Timestamp (UTC)**: {context_dict['as_of']}",
        "---",
    ]

    # 1. Fetch Quantitative Evidence Package from apps.quant_engine
    try:
        builder = EvidencePackageBuilder(symbol)
        quant_package = builder.build(persist_snapshot=False)
        m_state = quant_package.market_state
        f_state = quant_package.fundamental_state
        cot_state = quant_package.positioning_state
        seas_state = quant_package.seasonality

        context_dict["last_price"] = m_state.spot_price
        context_dict["return_1d"] = m_state.returns_1d
        context_dict["rvol"] = m_state.rvol
        context_dict["curve_state"] = m_state.curve_state
        context_dict["spread_f1_f2"] = m_state.prompt_spread_1m_2m

        markdown_sections.extend([
            "## 1. Verified Market State & Term Structure",
            f"- **Spot Reference**: ${m_state.spot_price:,.2f} | **1D Return**: {m_state.returns_1d:+.2%}",
            f"- **Multi-Horizon Returns**: 5D: {m_state.returns_5d:+.2%} | 21D: {m_state.returns_21d:+.2%} | 63D: {m_state.returns_63d:+.2%}",
            f"- **Realized Volatility**: {m_state.realized_vol_20d:.1f}%",
            f"- **Volume & OI**: RVOL {m_state.rvol:.2f}x | Volume Shock Z: {m_state.volume_shock_z:+.2f}σ | OI Regime: {m_state.oi_regime}",
            f"- **Forward Curve**: {m_state.curve_state.replace('_', ' ').upper()} | Prompt Spread (M1-M2): ${m_state.prompt_spread_1m_2m:+.3f} | 1Y Roll Yield: {m_state.roll_yield_1y:+.2%}",
            "",
        ])

        if f_state.storage_name:
            context_dict["fundamentals"] = {
                "variable_name": f_state.storage_name,
                "latest_value": f_state.storage_level,
                "deviation_pct": f_state.seasonal_percentile or 0.0,
                "momentum": f_state.balance_regime,
            }
            markdown_sections.extend([
                "## 2. Physical Supply / Demand Fundamentals",
                f"- **Variable**: {f_state.storage_name}",
                f"- **Latest Ingested Level**: {f_state.storage_level:,.1f} {f_state.storage_unit or ''}",
                f"- **Seasonal Percentile**: {f_state.seasonal_percentile or 'N/A'}",
                f"- **Balance Regime**: {f_state.balance_regime}",
                "",
            ])

        if cot_state.money_manager_net is not None:
            context_dict["cot_positioning"] = {
                "managed_money_net": cot_state.money_manager_net,
                "commercial_net": cot_state.commercial_net,
                "crowding_regime": cot_state.crowding_regime,
            }
            markdown_sections.extend([
                "## 3. CFTC Commitment of Traders (COT) Positioning",
                f"- **Managed Money Net**: {cot_state.money_manager_net:,} contracts ({cot_state.money_manager_net_pct_oi:+.1f}% of OI)",
                f"- **Commercial Net**: {cot_state.commercial_net:,} contracts",
                f"- **Crowding Regime**: {cot_state.crowding_regime}",
                "",
            ])

        if seas_state.directional_tendency:
            top_tenure = seas_state.directional_tendency
            context_dict["seasonality_tendency"] = {
                "tenure_window": top_tenure.tenure_window,
                "win_rate_pct": top_tenure.win_rate * 100.0,
                "mean_return_pct": top_tenure.mean_return,
                "t_stat": top_tenure.t_statistic,
            }
            markdown_sections.extend([
                "## 4. 20-Year Empirical Seasonality Expectations",
                f"- **Primary Forward Window**: {top_tenure.tenure_window}",
                f"- **Historical Win Rate**: {top_tenure.win_rate:.1%} (Mean Return: {top_tenure.mean_return:+.2%}, t-stat: {top_tenure.t_statistic:.2f})",
                "",
            ])

        if quant_package.divergences:
            div_list = []
            for d in quant_package.divergences:
                item_str = f"{d.type}: ({d.severity}) — {d.description}"
                div_list.append(item_str)
            context_dict["divergences"] = div_list
            markdown_sections.extend([
                "## 5. Active Quantitative Divergences",
                *[f"- {d}" for d in div_list],
                "",
            ])

    except Exception as exc:
        logger.warning("Could not assemble EvidencePackageBuilder for %s: %s", symbol, exc)

    # 2. Enrich with Live Quantitative Feature Package (RSI, ADX, EMAs, Multi-Factor Ratings)
    try:
        pipeline = FeaturePipeline()
        live_pkg = pipeline.extract_features(symbol)
        if live_pkg:
            context_dict["adx"] = live_pkg.trend.adx
            context_dict["trend"] = live_pkg.trend.trend_state
            context_dict["rsi"] = live_pkg.momentum.rsi
            context_dict["regime"] = live_pkg.regime.overall
            context_dict["composite_score"] = live_pkg.scores.overall_composite_score
            context_dict["vol_regime"] = live_pkg.volatility.regime

            live_md = format_llm_prompt_context(live_pkg)
            markdown_sections.extend([
                "## 6. Real-Time Quantitative Indicator Posture",
                live_md,
                "",
            ])
    except Exception as exc:
        logger.warning("Could not assemble LiveFeaturePackage for %s: %s", symbol, exc)

    # 3. Enrich with Macro Catalysts & News Intelligence from apps.news_intel
    try:
        upcoming_events = MarketCatalystEvent.objects.filter(
            status=EventStatus.SCHEDULED,
            primary_commodity=commodity,
        ).order_by("publication_time")[:3]

        if not upcoming_events.exists():
            upcoming_events = MarketCatalystEvent.objects.filter(
                status=EventStatus.SCHEDULED
            ).order_by("publication_time")[:3]

        catalyst_dicts = []
        if upcoming_events.exists():
            markdown_sections.append("## 7. Upcoming High-Impact Macro Catalysts")
            for ev in upcoming_events:
                cat_info = {
                    "title": ev.name,
                    "date": ev.publication_time.strftime("%Y-%m-%d %H:%M UTC") if ev.publication_time else "TBD",
                    "commodity": ev.primary_commodity.code if ev.primary_commodity else "MACRO",
                    "impact": ev.impact_level,
                }
                catalyst_dicts.append(cat_info)
                markdown_sections.append(f"- **{cat_info['title']}** [{cat_info['impact']} IMPACT] scheduled for {cat_info['date']}")
            markdown_sections.append("")
        context_dict["upcoming_catalysts"] = catalyst_dicts

        # Tagged news articles
        news_tags = NewsCommodityTag.objects.filter(
            commodity=commodity
        ).select_related("article").order_by("-article__published_at_utc")[:4]

        recent_news_list = []
        sentiment_scores = []
        if news_tags.exists():
            markdown_sections.append("## 8. Latest News Flow & Sentiment Analysis")
            for tag in news_tags:
                art = tag.article
                score = float(tag.commodity_sentiment_score)
                sentiment_scores.append(score)
                news_item = {
                    "headline": art.title,
                    "source": art.source_name,
                    "polarity": tag.commodity_sentiment,
                    "published": art.published_at_utc.strftime("%Y-%m-%d %H:%M") if art.published_at_utc else "",
                }
                recent_news_list.append(news_item)
                markdown_sections.append(f"- *[{art.source_name}]* **{art.title}** (Sentiment: {tag.commodity_sentiment})")
            markdown_sections.append("")

        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            context_dict["sentiment_score"] = round(avg_sentiment, 2)
            markdown_sections.append(f"- **Net Product Sentiment Barometer**: {avg_sentiment:+.2f} [-1.0 to +1.0]\n")

        context_dict["recent_news"] = recent_news_list

    except Exception as exc:
        logger.warning("Could not assemble News/Catalysts for %s: %s", symbol, exc)

    prompt_markdown = "\n".join(markdown_sections)
    return prompt_markdown, context_dict
