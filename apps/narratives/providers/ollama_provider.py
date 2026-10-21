"""
Local Ollama LangChain Provider Adapter.
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


class OllamaLangChainChatModel(BaseChatModel):
    """LangChain BaseChatModel for local Ollama generate endpoint."""
    base_url: str = "http://localhost:11434"
    model_name: str = "llama3"
    fallback_model: StaticLangChainChatModel = StaticLangChainChatModel()
    context_dict: Dict[str, Any] = {}

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt_text = "\n\n".join(m.content for m in messages if isinstance(m.content, str))
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt_text,
            "format": "json",
            "stream": False,
        }

        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "{}")
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])
        except Exception as exc:
            logger.info("Ollama API call failed or offline (%s). Falling back to StaticLangChainChatModel.", exc)
            self.fallback_model.context_dict = self.context_dict
            return self.fallback_model._generate(messages, stop, run_manager, **kwargs)

    @property
    def _llm_type(self) -> str:
        return "ollama-langchain-chat-model"


class OllamaLLMProvider(BaseLLMProvider):
    provider_name: str = "ollama"
    default_model: str = "llama3"

    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or getattr(settings, "OLLAMA_MODEL", self.default_model)
        self.fallback = StaticLLMProvider()
        self.chat_model = OllamaLangChainChatModel(
            base_url=self.base_url,
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
        url = f"{self.base_url.rstrip('/')}/api/generate"
        user_content = (
            f"SYSTEM: {system_instruction}\n\n"
            f"USER:\n{prompt}\n\n"
            "Return strictly valid JSON with keys: 'headline', 'executive_summary', 'market_context_body', "
            "'key_bullet_points', 'risk_factors'."
        )
        payload = {
            "model": self.model,
            "prompt": user_content,
            "format": "json",
            "stream": False,
        }

        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "{}")
                parsed = json.loads(text)

                return LLMResponse(
                    headline=parsed.get("headline", "Market Intelligence Briefing"),
                    executive_summary=parsed.get("executive_summary", ""),
                    market_context_body=parsed.get("market_context_body", ""),
                    key_bullet_points=parsed.get("key_bullet_points", []),
                    risk_factors=parsed.get("risk_factors", []),
                    provider_name=self.provider_name,
                    model_name=self.model,
                    prompt_tokens=data.get("prompt_eval_count", len(prompt.split())),
                    completion_tokens=data.get("eval_count", len(text.split())),
                    raw_response=data,
                )
        except Exception as exc:
            logger.info("Ollama API call failed or offline (%s). Falling back to StaticLLMProvider.", exc)
            return self.fallback.generate_narrative(prompt, system_instruction, context_dict, narrative_type)
