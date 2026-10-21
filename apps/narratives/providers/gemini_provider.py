"""
Google Gemini LangChain Provider Adapter.
"""
import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from django.conf import settings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun

from .base import BaseLLMProvider, LLMResponse
from .static_catalog import StaticLLMProvider, StaticLangChainChatModel

logger = logging.getLogger(__name__)


class GeminiLangChainChatModel(BaseChatModel):
    """LangChain BaseChatModel for Google Gemini REST endpoint."""
    api_key: str = ""
    model_name: str = "gemini-2.0-flash"
    fallback_model: StaticLangChainChatModel = StaticLangChainChatModel()
    context_dict: Dict[str, Any] = {}

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if not self.api_key:
            self.fallback_model.context_dict = self.context_dict
            return self.fallback_model._generate(messages, stop, run_manager, **kwargs)

        prompt_text = "\n\n".join(m.content for m in messages if isinstance(m.content, str))
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])
        except Exception as exc:
            logger.warning("Gemini API call failed (%s). Falling back to StaticLangChainChatModel.", exc)
            self.fallback_model.context_dict = self.context_dict
            return self.fallback_model._generate(messages, stop, run_manager, **kwargs)

    @property
    def _llm_type(self) -> str:
        return "gemini-langchain-chat-model"


class GeminiLLMProvider(BaseLLMProvider):
    provider_name: str = "gemini"
    default_model: str = "gemini-2.0-flash"

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "")
        self.model = model or getattr(settings, "GEMINI_MODEL", self.default_model)
        self.fallback = StaticLLMProvider()
        self.chat_model = GeminiLangChainChatModel(
            api_key=self.api_key,
            model_name=self.model,
        )

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
        if not self.api_key:
            logger.info("GEMINI_API_KEY not set. Using StaticLLMProvider fallback.")
            return self.fallback.generate_narrative(prompt, system_instruction, context_dict, narrative_type)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        json_prompt = (
            f"{prompt}\n\n"
            "Return a strictly valid JSON object with keys: 'headline', 'executive_summary', 'market_context_body', "
            "'key_bullet_points', 'risk_factors'."
        )
        payload = {
            "contents": [{"parts": [{"text": json_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                usage = data.get("usageMetadata", {})

                return LLMResponse(
                    headline=parsed.get("headline", "Market Intelligence Briefing"),
                    executive_summary=parsed.get("executive_summary", ""),
                    market_context_body=parsed.get("market_context_body", ""),
                    key_bullet_points=parsed.get("key_bullet_points", []),
                    risk_factors=parsed.get("risk_factors", []),
                    provider_name=self.provider_name,
                    model_name=self.model,
                    prompt_tokens=usage.get("promptTokenCount", len(prompt.split())),
                    completion_tokens=usage.get("candidatesTokenCount", len(text.split())),
                    raw_response=data,
                )
        except Exception as exc:
            logger.warning("Gemini API call failed (%s). Falling back to StaticLLMProvider.", exc)
            return self.fallback.generate_narrative(prompt, system_instruction, context_dict, narrative_type)
