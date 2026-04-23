"bot/agents/schemas.py"

from typing import List, Optional
from pydantic import BaseModel, Field

class ToneResult(BaseModel):
    """
    Result of a tone analysis.
    score: float 0.0 to 1.0 (professionalism)
    flags: specific tone markers (e.g. "aggressive", "casual")
    """
    score: float = Field(..., ge=0.0, le=1.0)
    flags: List[str] = Field(default_factory=list)

class DraftSuggestion(BaseModel):
    """
    AI-improved draft content.
    """
    improved_text: str
    diff: str

class FaqMatch(BaseModel):
    """
    Result of an FAQ semantic lookup.
    """
    matched: bool
    answer: Optional[str] = None
    confidence: float = 0.0

class SpamResult(BaseModel):
    """
    Classification result for spam detection.
    """
    is_spam: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
