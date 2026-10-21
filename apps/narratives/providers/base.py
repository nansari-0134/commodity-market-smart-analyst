"""
Base Abstract LangChain LLM Provider and Data Transfer Objects.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel


@dataclass
class LLMResponse:
    """Normalized response payload returned by all LLM providers."""
    headline: str
    executive_summary: str
    market_context_body: str
    key_bullet_points: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    provider_name: str = "base"
    model_name: str = "default"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw_response: Dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """
    Abstract base provider interface enforcing Source Independence (Directive 1)
    and powered by LangChain Chat Model abstractions.
    """
    provider_name: str = "base"
    default_model: str = "default"

    @abstractmethod
    def get_langchain_model(self) -> BaseChatModel:
        """Returns the underlying LangChain BaseChatModel instance."""
        pass

    @abstractmethod
    def generate_narrative(
        self,
        prompt: str,
        system_instruction: str,
        context_dict: Dict[str, Any],
        narrative_type: str = "MORNING_BRIEF",
    ) -> LLMResponse:
        """
        Generate structured market narrative from prompt and context.
        """
        pass
