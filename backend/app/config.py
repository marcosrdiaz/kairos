"""Configuración de la app desde variables de entorno (`.env`). Ver `.env.example`."""

from datetime import datetime
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
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

    market_data_provider: Literal["offline", "yahoo"] = "offline"
    """`offline`: CSV de `data/prices` (demo). `yahoo`: precios en directo (D-065)."""
    market_data_api_key: str = ""

    database_url: str = "postgresql+psycopg://kairos:kairos@localhost:5432/kairos"

    news_poll_minutes: int = Field(default=5, ge=1)
    """Cada cuánto busca noticias el servicio `news-updater` y lee los RSS (TB-01)."""
    news_google_minutes: int = Field(default=15, ge=1)
    """Cada cuánto se busca en Google Noticias (17 búsquedas por pasada; decisión de TB-01)."""

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

    @model_validator(mode="after")
    def _production_needs_live_prices(self) -> "Settings":
        """Sin modo demo, los precios del CSV serían viejos presentados como actuales (D-065)."""
        if not self.demo_mode and self.market_data_provider == "offline":
            raise ValueError(
                "DEMO_MODE=false necesita precios en directo: pon MARKET_DATA_PROVIDER=yahoo "
                "(o vuelve a DEMO_MODE=true para usar los CSV de data/prices)"
            )
        return self

    @property
    def mode(self) -> Literal["demo", "production"]:
        return "demo" if self.demo_mode else "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
