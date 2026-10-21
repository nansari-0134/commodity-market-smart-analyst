"""
Deterministic LangChain Static LLM Provider.

Implements an institutional LangChain BaseChatModel that synthesizes
structured JSON financial research narratives directly from ground-truth
evidence without external network calls.
"""
import json
from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun

from .base import BaseLLMProvider, LLMResponse


def synthesize_deterministic_narrative(context_dict: Dict[str, Any], narrative_type: str = "MORNING_BRIEF") -> Dict[str, Any]:
    """Helper function to build deterministic structured output."""
    commodity_code = context_dict.get("commodity_code", "COMMODITIES")
    commodity_name = context_dict.get("commodity_name", "Global Commodity Complex")
    last_price = context_dict.get("last_price", 0.0)
    return_1d = context_dict.get("return_1d", 0.0)
    regime = str(context_dict.get("regime", "NEUTRAL")).upper()
    trend = context_dict.get("trend", "rangebound")
    vol_regime = context_dict.get("vol_regime", "normal")
    curve_state = str(context_dict.get("curve_state", "FLAT")).upper()
    spread_f1_f2 = context_dict.get("spread_f1_f2", 0.0)
    adx = context_dict.get("adx", 20.0)
    rsi = context_dict.get("rsi", 50.0)
    rvol = context_dict.get("rvol", 1.0)
    composite_score = context_dict.get("composite_score", 0.0)
    divergences = context_dict.get("divergences", [])
    fundamentals = context_dict.get("fundamentals", {})
    catalysts = context_dict.get("upcoming_catalysts", [])
    sentiment_score = context_dict.get("sentiment_score", 0.0)

    # Build headline
    if narrative_type == "RISK_ALERT" or (divergences and len(divergences) > 0):
        headline = f"{commodity_name} ({commodity_code}): Quantitative Divergence Alert Amid {curve_state} Regime"
    elif composite_score >= 0.35:
        headline = f"{commodity_name} ({commodity_code}): Structural Bullish Asymmetry on {curve_state} & Positive Momentum"
    elif composite_score <= -0.35:
        headline = f"{commodity_name} ({commodity_code}): Distribution Pressure & Bearish Momentum Dominating Structure"
    else:
        headline = f"{commodity_name} ({commodity_code}): Rangebound Equilibrium with {curve_state} Term Structure"

    # Build executive summary
    sentiment_label = "bullish" if sentiment_score > 0.15 else ("bearish" if sentiment_score < -0.15 else "balanced")
    exec_summary = (
        f"{commodity_name} is trading at ${last_price:,.2f} ({return_1d:+.2%}), characterized by a {regime} "
        f"regime with an overall multi-factor score of {composite_score:+.2f}. The futures curve exhibits "
        f"{curve_state} with prompt calendar spread at ${spread_f1_f2:+.3f}. Physical inventory levels and "
        f"macro catalyst sentiment remain {sentiment_label}, presenting defined risk parameters across the complex."
    )

    # Build market context body (Markdown)
    body_sections = [
        f"## Market Structure & Quantitative State",
        f"The asset maintains an ADX(14) reading of {adx:.1f} indicating {trend} conditions, while RSI(14) sits at {rsi:.1f}. "
        f"Trading activity reflects a relative volume (RVOL) of {rvol:.2f}x with annualized realized volatility categorizing "
        f"current market conditions as {vol_regime}.",
        "",
        f"## Term Structure & Spread Mechanics",
        f"The forward curve is currently in **{curve_state}**. Prompt contract spread (F1-F2) stands at ${spread_f1_f2:+.3f}, "
        f"reflecting spot physical tightness and roll yield implications for derivatives positioning.",
    ]

    if fundamentals:
        var_name = fundamentals.get("variable_name", "Physical Stocks")
        dev_pct = fundamentals.get("deviation_pct", 0.0)
        dev_sign = "+" if dev_pct >= 0 else ""
        body_sections.extend([
            "",
            "## Fundamental Balance & Storage Levels",
            f"Primary fundamental tracking for {var_name} indicates a {dev_sign}{dev_pct:.1f}% deviation relative to 5-year seasonal normal levels. "
            f"Storage momentum is assessed as {fundamentals.get('momentum', 'stable').upper()}."
        ])

    if catalysts:
        body_sections.extend([
            "",
            "## Macro Catalysts & Market Events",
            "Upcoming high-impact events identified on the institutional calendar:",
        ])
        for cat in catalysts[:3]:
            body_sections.append(f"- **{cat.get('title', 'Event')}** ({cat.get('date', 'Upcoming')}): Expected impact on {cat.get('commodity', commodity_code)}")

    market_context_body = "\n".join(body_sections)

    # Build key bullet points
    bullets = [
        f"Price / Return: Spot reference at ${last_price:,.2f} ({return_1d:+.2%} on the session).",
        f"Curve Regime: Forward curve in {curve_state} with M1-M2 prompt spread at ${spread_f1_f2:+.3f}.",
        f"Quant Posture: Composite rating {composite_score:+.2f} with RSI(14) at {rsi:.1f} and RVOL {rvol:.2f}x.",
    ]
    if divergences:
        for div in divergences[:2]:
            bullets.append(f"Divergence Flag: {div}")

    # Build risk factors
    risks = [
        f"Macro Factor Volatility: Shift in broader macroeconomic indicators or US Dollar index.",
        f"Storage Rebalancing Risk: Deviation from seasonal normal could trigger prompt curve inversion.",
        f"Execution & Liquidity: RVOL at {rvol:.2f}x with potential slippage around upcoming scheduled economic prints.",
    ]

    return {
        "headline": headline,
        "executive_summary": exec_summary,
        "market_context_body": market_context_body,
        "key_bullet_points": bullets,
        "risk_factors": risks,
    }


class StaticLangChainChatModel(BaseChatModel):
    """
    LangChain BaseChatModel implementation providing deterministic synthesis.
    """
    model_name: str = "deterministic-langchain-engine-v1"
    context_dict: Dict[str, Any] = {}

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Build synthesis from context_dict or fallback
        payload = synthesize_deterministic_narrative(self.context_dict)
        content_json = json.dumps(payload)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content_json))])

    @property
    def _llm_type(self) -> str:
        return "static-langchain-chat-model"


class StaticLLMProvider(BaseLLMProvider):
    provider_name: str = "static"
    default_model: str = "deterministic-langchain-engine-v1"

    def __init__(self):
        self.chat_model = StaticLangChainChatModel()

    def get_langchain_model(self) -> BaseChatModel:
        return self.chat_model

    def generate_narrative(
        self,
        prompt: str,
        system_instruction: str,
        context_dict: Dict[str, Any],
        narrative_type: str = "MORNING_BRIEF",
    ) -> LLMResponse:
        self.chat_model.context_dict = context_dict
        payload = synthesize_deterministic_narrative(context_dict, narrative_type)

        return LLMResponse(
            headline=payload["headline"],
            executive_summary=payload["executive_summary"],
            market_context_body=payload["market_context_body"],
            key_bullet_points=payload["key_bullet_points"],
            risk_factors=payload["risk_factors"],
            provider_name=self.provider_name,
            model_name=self.default_model,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(payload["market_context_body"].split()) + len(payload["executive_summary"].split()),
            raw_response={"status": "success", "framework": "langchain", "mode": "deterministic_synthesis"},
        )
