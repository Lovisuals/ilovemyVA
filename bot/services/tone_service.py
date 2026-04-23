"bot/services/tone_service.py"

from bot.config import settings
from bot.agents.schemas import ToneResult
from bot.agents.gemini_client import GeminiClient

class ToneService:
    @staticmethod
    async def score(text: str) -> ToneResult:
        if not settings.ai_enabled:
            return ToneResult(score=1.0, flags=["ai_disabled"])

        client = GeminiClient()
        try:
            return await client.score_tone(text)
        except Exception:
            return ToneResult(score=1.0, flags=["service_unavailable"])
