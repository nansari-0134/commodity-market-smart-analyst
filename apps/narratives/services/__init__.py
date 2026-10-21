"""
Narratives services initialization.
"""
from .context_builder import build_narrative_context
from .generator import generate_market_narrative

__all__ = [
    "build_narrative_context",
    "generate_market_narrative",
]
