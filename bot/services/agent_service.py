"bot/services/agent_service.py"

from bot.config import settings
from bot.agents.schemas import ToneResult, SpamResult, DraftSuggestion, FaqMatch
from bot.agents.gemini_client import GeminiClient

class AgentService:
    @staticmethod
    async def run_tone_check(text: str) -> ToneResult:
        if not settings.ai_enabled:
            return ToneResult(score=1.0, flags=["ai_disabled"])
        client = GeminiClient()
        try:
            return await client.score_tone(text)
        except Exception:
            return ToneResult(score=1.0, flags=["unavailable"])

    @staticmethod
    async def run_spam_classify(text: str) -> SpamResult:
        if not settings.ai_enabled:
            return SpamResult(is_spam=False, confidence=0.0)
        client = GeminiClient()
        try:
            return await client.classify_spam(text)
        except Exception:
            return SpamResult(is_spam=False, confidence=0.0)

    @staticmethod
    async def run_draft_suggestion(text: str) -> DraftSuggestion:
        if not settings.ai_enabled:
            return DraftSuggestion(improved_text=text, diff="")
        # Roadmap v1.4 - Placeholder logic that still returns a valid object
        return DraftSuggestion(improved_text=text, diff="")

    @staticmethod
    async def run_faq_match(text: str) -> FaqMatch:
        if not settings.ai_enabled:
            return FaqMatch(matched=False, confidence=0.0)
        # Roadmap v1.4 - Placeholder logic that still returns a valid object
        return FaqMatch(matched=False, confidence=0.0)
