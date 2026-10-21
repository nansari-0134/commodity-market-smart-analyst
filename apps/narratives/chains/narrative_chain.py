"""
LangChain LCEL Narrative Chain Execution Engine.

Composes:
ChatPromptTemplate | BaseChatModel | PydanticOutputParser(NarrativeOutputSchema)
"""
import logging
from typing import Any, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from apps.narratives.chains.schemas import NarrativeOutputSchema
from apps.narratives.providers.base import LLMResponse
from apps.narratives.providers.factory import get_llm_provider

logger = logging.getLogger(__name__)

SYSTEM_RESEARCH_INSTRUCTION = """
You are a senior institutional commodity derivatives market strategist and quantitative surveillance analyst.
Your objective is to synthesize a rigorous, factual executive briefing based exclusively on the provided GROUND-TRUTH MARKET EVIDENCE.

CRITICAL DIRECTIVES:
1. STRICT ADHERENCE TO FACTS: Never invent, extrapolate, or hallucinate numerical figures, inventory levels, or prices.
2. ZERO MENTAL ARITHMETIC: All returns, curve spreads, and volatility percentiles have been computed deterministically. Cite them exactly as given.
3. INSTITUTIONAL REASONING: Explain the transmission mechanism between term structure (backwardation/contango), physical inventory momentum, and quantitative momentum.
4. REGULATORY MANDATE: Do NOT formulate trade recommendations, price targets, or buy/sell calls. Maintain an objective, institutional surveillance perspective.
"""


def create_narrative_chain(provider_name: Optional[str] = None):
    """
    Constructs a LangChain LCEL Runnable pipeline.
    """
    provider = get_llm_provider(provider_name)
    chat_model = provider.get_langchain_model()
    parser = PydanticOutputParser(pydantic_object=NarrativeOutputSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_RESEARCH_INSTRUCTION.strip()),
        ("human", "{evidence_context}\n\nFormat your output strictly according to the following schema:\n{format_instructions}"),
    ])

    chain = prompt | chat_model | parser
    return chain, parser, provider


def execute_narrative_chain(
    prompt_markdown: str,
    context_dict: Dict[str, Any],
    provider_name: Optional[str] = None,
    narrative_type: str = "MORNING_BRIEF",
) -> LLMResponse:
    """
    Executes the LangChain pipeline to produce a validated LLMResponse.
    """
    provider = get_llm_provider(provider_name)
    
    # Configure the static fallback / provider model with context_dict
    model = provider.get_langchain_model()
    if hasattr(model, "context_dict"):
        model.context_dict = context_dict

    parser = PydanticOutputParser(pydantic_object=NarrativeOutputSchema)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_RESEARCH_INSTRUCTION.strip()),
        ("human", "{evidence_context}\n\nStrict JSON Format Instructions:\n{format_instructions}"),
    ])

    chain = prompt | model | parser

    try:
        parsed_output: NarrativeOutputSchema = chain.invoke({
            "evidence_context": prompt_markdown,
            "format_instructions": parser.get_format_instructions(),
        })

        return LLMResponse(
            headline=parsed_output.headline,
            executive_summary=parsed_output.executive_summary,
            market_context_body=parsed_output.market_context_body,
            key_bullet_points=parsed_output.key_bullet_points,
            risk_factors=parsed_output.risk_factors,
            provider_name=provider.provider_name,
            model_name=provider.default_model,
            prompt_tokens=len(prompt_markdown.split()),
            completion_tokens=len(parsed_output.market_context_body.split()) + len(parsed_output.executive_summary.split()),
            raw_response={"framework": "langchain_lcel", "status": "success"},
        )
    except Exception as exc:
        logger.warning("LangChain LCEL chain failed (%s). Executing provider fallback.", exc)
        return provider.generate_narrative(
            prompt=prompt_markdown,
            system_instruction=SYSTEM_RESEARCH_INSTRUCTION.strip(),
            context_dict=context_dict,
            narrative_type=narrative_type,
        )
