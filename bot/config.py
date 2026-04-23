"bot/config.py"

import os
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class BotSettings(BaseSettings):
    token: str = Field(..., alias="BOT_TOKEN")
    owner_id: int = Field(..., alias="OWNER_ID")
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")
    webhook_url: Optional[str] = Field(None, alias="WEBHOOK_URL")
    port: int = Field(8080, alias="PORT")
    storage_channel_id: int = Field(..., alias="STORAGE_CHANNEL_ID")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(i.strip()) for i in v.split(",") if i.strip()]
        return v

class DatabaseSettings(BaseSettings):
    url: str = Field(..., alias="DATABASE_URL")
    pool_size: int = 10
    pool_timeout: int = 30
    echo: bool = False

    @property
    def dsn(self) -> str:
        url = self.url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

class AISettings(BaseSettings):
    antigravity_api_key: Optional[str] = Field(None, alias="ANTIGRAVITY_API_KEY")
    gemini_api_key: Optional[str] = Field(None, alias="GEMINI_API_KEY")
    gemini_model: str = "gemini-flash-3"
    temperature: float = 0.1
    max_tokens: int = 1024
    timeout_ms: int = 3000

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot: BotSettings
    database: DatabaseSettings
    ai: AISettings

    @property
    def ai_enabled(self) -> bool:
        return bool(self.ai.antigravity_api_key and self.ai.gemini_api_key)

    @property
    def redis_url(self) -> Optional[str]:
        return os.getenv("REDIS_URL")

settings = Settings(
    bot=BotSettings(),
    database=DatabaseSettings(),
    ai=AISettings()
)
