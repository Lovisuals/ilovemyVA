from typing import List, Optional
from pydantic import BaseModel, Field


class ToneResult(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    flags: List[str] = Field(default_factory=list)


class DraftSuggestion(BaseModel):
    improved_text: str
    diff: str


class FaqMatch(BaseModel):
    matched: bool
    answer: Optional[str] = None
    confidence: float = 0.0


class SpamResult(BaseModel):
    is_spam: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
