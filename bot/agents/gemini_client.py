import json
import asyncio
from typing import Type, TypeVar
import google.generativeai as genai
from pydantic import BaseModel
from bot.config import settings
from bot.agents.schemas import ToneResult, SpamResult

T = TypeVar("T", bound=BaseModel)

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.ai.gemini_api_key)
        self.model = genai.GenerativeModel(settings.ai.gemini_model)

    async def _call_api(self, prompt: str, schema: Type[T]) -> T:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.ai.temperature,
                    max_output_tokens=settings.ai.max_tokens,
                    response_mime_type="application/json",
                )
            ),
            timeout=settings.ai.timeout_ms / 1000.0
        )
        data = json.loads(response.text)
        return schema.model_validate(data)

    async def score_tone(self, text: str) -> ToneResult:
        prompt = (
            f"Analyze the tone of this medical content. Score professionalism (0.0-1.0). "
            f"Return JSON with \"score\" and \"flags\" (list of strings). "
            f"Content: {text}"
        )
        return await self._call_api(prompt, ToneResult)

    async def classify_spam(self, text: str) -> SpamResult:
        prompt = (
            f"Classify if this message is spam. Return JSON with \"is_spam\" (bool) "
            f"and \"confidence\" (0.0-1.0). Message: {text}"
        )
        return await self._call_api(prompt, SpamResult)
