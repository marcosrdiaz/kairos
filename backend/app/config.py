"""Configuración de la app desde variables de entorno (`.env`). Ver `.env.example`."""

from datetime import datetime
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model_fast: str = "claude-haiku-5-5"
    anthropic_model_deep: str = "claude-sonnet-5-5"

    elevenlabs_api_key: str = ""
    elevenlabs_stt_model: str = ""
    elevenlabs_tts_model: str = ""
    elevenlabs_voice_id: str = ""

    market_data_provider: str = "offline"
    market_data_api_key: str = ""

    database_url: str = "postgresql+psycopg://kairos:kairos@localhost:5432/kairos"

    demo_mode: bool = True
    demo_clock: datetime | None = None

    @field_validator("demo_clock", mode="before")
    @classmethod
    def _empty_clock_is_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @field_validator("demo_clock")
    @classmethod
    def _clock_needs_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("DEMO_CLOCK debe llevar zona horaria (p. ej. 2026-11-08T18:00:00Z)")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
