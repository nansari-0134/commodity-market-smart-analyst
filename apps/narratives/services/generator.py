"""
Market Narrative Generator Service Powered by LangChain.

Orchestrates context aggregation, system prompt enforcement, LangChain LCEL pipeline execution,
regulatory disclaimer attachment, and point-in-time database persistence.
"""
import logging
from typing import Optional
from django.utils import timezone

from apps.commodities.models import CommodityMaster
from apps.narratives.models import (
    MarketNarrative,
    NarrativeType,
    NarrativeStatus,
    REGULATORY_COMPLIANCE_DISCLAIMER,
)
from apps.narratives.chains.narrative_chain import execute_narrative_chain
from .context_builder import build_narrative_context

logger = logging.getLogger(__name__)


def generate_market_narrative(
    commodity_code: str = "CL",
    narrative_type: str = NarrativeType.MORNING_BRIEF,
    provider_name: Optional[str] = None,
) -> MarketNarrative:
    """
    Generates and persists an evidence-grounded MarketNarrative using LangChain.
    """
    symbol = (commodity_code or "CL").upper().strip()
    commodity = CommodityMaster.objects.filter(code=symbol).first()

    # 1. Compile ground-truth multi-source context
    prompt_markdown, context_dict = build_narrative_context(symbol)

    # 2. Execute via LangChain LCEL pipeline
    logger.info("Executing LangChain narrative chain for %s (provider: %s)", symbol, provider_name or "default")
    response = execute_narrative_chain(
        prompt_markdown=prompt_markdown,
        context_dict=context_dict,
        provider_name=provider_name,
        narrative_type=narrative_type,
    )

    # 3. Enforce mandatory compliance and persist immutable PointInTime record
    narrative = MarketNarrative.objects.create(
        commodity=commodity,
        narrative_type=narrative_type,
        headline=response.headline,
        executive_summary=response.executive_summary,
        market_context_body=response.market_context_body,
        key_bullet_points=response.key_bullet_points,
        risk_factors=response.risk_factors,
        evidence_snapshot=context_dict,
        llm_provider=response.provider_name,
        llm_model=response.model_name,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        status=NarrativeStatus.PUBLISHED,
        compliance_disclaimer=REGULATORY_COMPLIANCE_DISCLAIMER,
        availability_time=timezone.now(),
    )

    logger.info("Successfully published MarketNarrative %s for %s via LangChain", narrative.id, symbol)
    return narrative
