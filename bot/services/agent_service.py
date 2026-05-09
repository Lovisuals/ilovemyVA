from typing import List, Optional
from pydantic import BaseModel
class ToneResult(BaseModel):
    score: float = 1.0
    flags: List[str] = []
class SpamResult(BaseModel):
    is_spam: bool = False
    confidence: float = 0.0
class DraftSuggestion(BaseModel):
    improved_text: str
    diff: str = ""
class FaqMatch(BaseModel):
    matched: bool = False
    confidence: float = 0.0
class AgentService:
    @staticmethod
    async def run_tone_check(text: str) -> ToneResult:
        return ToneResult(score=1.0, flags=["ai_disabled"])
    @staticmethod
    async def run_spam_classify(text: str) -> SpamResult:
        return SpamResult(is_spam=False, confidence=0.0)
    @staticmethod
    async def run_draft_suggestion(text: str) -> DraftSuggestion:
        return DraftSuggestion(improved_text=text, diff="")
    @staticmethod
    async def run_faq_match(text: str) -> FaqMatch:
        return FaqMatch(matched=False, confidence=0.0)
