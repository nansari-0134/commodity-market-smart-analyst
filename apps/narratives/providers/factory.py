"""
Factory resolver for Pluggable LLM Providers.
"""
from typing import Dict, Type
from django.conf import settings
from .base import BaseLLMProvider
from .static_catalog import StaticLLMProvider
from .gemini_provider import GeminiLLMProvider
from .claude_provider import ClaudeLLMProvider
from .openai_provider import OpenAILLMProvider
from .ollama_provider import OllamaLLMProvider

PROVIDER_REGISTRY: Dict[str, Type[BaseLLMProvider]] = {
    "static": StaticLLMProvider,
    "gemini": GeminiLLMProvider,
    "claude": ClaudeLLMProvider,
    "openai": OpenAILLMProvider,
    "ollama": OllamaLLMProvider,
}


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """
    Instantiates and returns the configured LLM provider.
    
    If provider_name is not provided, defaults to settings.LLM_PROVIDER (or 'static').
    If an unknown provider is specified, falls back gracefully to StaticLLMProvider.
    """
    key = (provider_name or getattr(settings, "LLM_PROVIDER", "static")).lower().strip()
    provider_cls = PROVIDER_REGISTRY.get(key, StaticLLMProvider)
    return provider_cls()
