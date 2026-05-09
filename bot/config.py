import os
import hashlib
from dotenv import load_dotenv
load_dotenv()
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
class BotSettings(BaseSettings):
    token: str = Field(..., alias="BOT_TOKEN")
    owner_id: int = Field(..., alias="OWNER_ID")
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")
    webhook_url: Optional[str] = Field(None, alias="WEBHOOK_URL")
    webhook_secret: Optional[str] = Field(None, alias="WEBHOOK_SECRET")
    port: int = Field(8080, alias="PORT")
    storage_channel_id: int = Field(..., alias="STORAGE_CHANNEL_ID")
    main_channel_id: int = Field(..., alias="MAIN_CHANNEL_ID")
    @field_validator("webhook_url", mode="before")
    @classmethod
    def resolve_webhook_url(cls, v):
        if v:
            return v
        domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        if domain:
            return f"https://{domain}"
        return None
    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(i.strip()) for i in v.split(",") if i.strip()]
        return v
    @field_validator("webhook_secret", mode="before")
    @classmethod
    def resolve_webhook_secret(cls, v):
        if v:
            return v
        token = os.getenv("BOT_TOKEN", "")
        if not token:
            return None
        return hashlib.sha256(token.encode("utf-8")).hexdigest()[:32]
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
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    bot: BotSettings
    database: DatabaseSettings
    @property
    def redis_url(self) -> Optional[str]:
        return os.getenv("REDIS_URL")
settings = Settings(
    bot=BotSettings(),
    database=DatabaseSettings()
)
