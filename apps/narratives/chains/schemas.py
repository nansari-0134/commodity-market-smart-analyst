"""
Strict Pydantic Output Schemas for LangChain Parsers.
"""
from typing import List
from pydantic import BaseModel, Field


class NarrativeOutputSchema(BaseModel):
    """Structured financial narrative parsed by LangChain PydanticOutputParser."""
    headline: str = Field(
        ...,
        description="Concise institutional headline capturing core market dynamic and curve posture",
    )
    executive_summary: str = Field(
        ...,
        description="2-3 sentence executive synopsis summarizing spot level, return, curve slope, and posture",
    )
    market_context_body: str = Field(
        ...,
        description="Structured Markdown narrative analyzing market state, term structure, fundamentals, and catalysts",
    )
    key_bullet_points: List[str] = Field(
        default_factory=list,
        description="High-conviction quantitative bullets / takeaways citing exact verified numbers",
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Surveillance risk vectors, structural asymmetries, and catalyst triggers",
    )
