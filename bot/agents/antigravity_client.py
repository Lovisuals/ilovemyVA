"bot/agents/antigravity_client.py"

import json
import httpx
import asyncio
from typing import Type, TypeVar
from pydantic import BaseModel
from bot.config import settings
from bot.agents.schemas import DraftSuggestion

T = TypeVar("T", bound=BaseModel)

class AntigravityClient:
    def __init__(self):
        self.api_key = settings.ai.antigravity_api_key
        self.base_url = "https://api.antigravity.ai/v1"

    async def _call_api(self, endpoint: str, data: dict, schema: Type[T]) -> T:
        async with httpx.AsyncClient(timeout=settings.ai.timeout_ms / 1000.0) as client:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return schema.model_validate(response.json())

    async def get_draft_suggestion(self, text: str) -> DraftSuggestion:
        return await self._call_api(
            "/suggest",
            {"content": text, "tone": "professional_medical"},
            DraftSuggestion
        )
