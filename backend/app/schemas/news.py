"""Contratos de noticias (T4-27, hito E).

Una noticia (`NewsItemOut`) se ve siempre desde una cartera: `GET /portfolios/{id}/news`. Lleva
dos partes que salen de sitios distintos:

- **Clasificación** (`category`, `companies`, `asset_ids`, `channels`, `causal_chain`,
  `relevance`): la hace el agente clasificador (T4-29). **No contiene ningún número** (regla 1):
  un validador rechaza dígitos en los textos que redacta el agente, como en `EventAnalysis`.
- **Estimación** (`estimate`): la calcula el motor de impacto (T4-30) con datos históricos, nunca
  el LLM. Rango en € y en fracción del valor de la cartera, plazo en sesiones, desde cuándo se nota
  en cada posición, confianza y `calc_id`. Cuando el evento ya tiene el shock medido (T4-04), pasa a
  `measured`.

Cada cartera es independiente: las cifras de `estimate` son siempre de la cartera de la ruta.
"""

import re
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from app.schemas.common import (
    Confidence,
    ContractModel,
    Factor,
    Fraction,
    Money,
    Polarity,
    SourceRef,
    UtcDatetime,
)
from app.schemas.events import CompanyRef, Relevance

_DIGIT = re.compile(r"\d")


class NewsCategory(StrEnum):
    """Filtros de la pantalla Noticias."""

    COMPANY = "company"  # noticias de empresa (producto, regulación, directivos...)
    EARNINGS = "earnings"  # resultados
    CENTRAL_BANK = "central_bank"  # BCE, Reserva Federal...
    POLITICS = "politics"  # política, aranceles, elecciones
    COMMODITIES = "commodities"  # petróleo, gas, materias primas
    FX = "fx"  # divisas
    OTHER = "other"


class NewsDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    UNCERTAIN = "uncertain"


class NewsEstimateStatus(StrEnum):
    ESTIMATED = "estimated"  # rango estimado con datos históricos, antes de medirlo
    MEASURED = "measured"  # el evento ya tiene shock medido con cierres (T4-04)
    PENDING = "pending"  # clasificada, pero aún sin estimación
    NOT_RELEVANT = "not_relevant"  # no toca ningún activo ni factor de esta cartera


class NewsEstimateMethod(StrEnum):
    ANALOGS = "analogs"  # eventos parecidos del histórico
    VOLATILITY = "volatility"  # sin análogos suficientes: volatilidad histórica al plazo
    MEASURED = "measured"  # shock medido con cierres (T4-04)


class EffectTiming(StrEnum):
    """Cuándo se nota en una posición, según su `price_kind`."""

    SAME_SESSION = "same_session"  # acciones y ETF: en la sesión
    NEXT_NAV = "next_nav"  # fondos: con el siguiente valor liquidativo
    NO_DAILY_PRICE = "no_daily_price"  # depósitos y similares: sin precio diario


class NewsChannel(ContractModel):
    """Por dónde llega la noticia a la cartera: un factor o una empresa, con su dirección.

    Exactamente uno de `factor` y `company_key`.
    """

    factor: Factor | None = None
    company_key: str | None = None
    direction: NewsDirection
    label: str
    rationale: str

    @field_validator("label", "rationale")
    @classmethod
    def _no_digits(cls, value: str) -> str:
        if _DIGIT.search(value):
            raise ValueError("La clasificación no lleva números (regla 1)")
        return value

    @model_validator(mode="after")
    def _one_target(self) -> "NewsChannel":
        if (self.factor is None) == (self.company_key is None):
            raise ValueError("Un canal es de un factor o de una empresa, no de los dos")
        return self


class NewsPositionEstimate(ContractModel):
    """Efecto estimado en una posición de la cartera."""

    asset_id: str
    name: str
    impact_eur: Money
    low_eur: Money
    high_eur: Money
    timing: EffectTiming
    effective_from: UtcDatetime | None


class NewsEstimateOut(ContractModel):
    """Impacto estimado de la noticia en la cartera de la ruta.

    - `estimated` y `measured`: llevan importes, fracciones, confianza, método y `calc_id`;
      `low_eur ≤ impact_eur ≤ high_eur`.
    - `pending` y `not_relevant`: sin ninguna cifra.
    - `*_pct` son fracciones del valor de la cartera ("-0.012" = −1,2 %).
    - `horizon_sessions`: plazo al que se refiere el rango (p. ej. 5 sesiones).
    - `event_id`: el evento medido, cuando lo hay.
    """

    status: NewsEstimateStatus
    polarity: Polarity | None = None
    impact_eur: Money | None = None
    low_eur: Money | None = None
    high_eur: Money | None = None
    impact_pct: Fraction | None = None
    low_pct: Fraction | None = None
    high_pct: Fraction | None = None
    horizon_sessions: int | None = None
    confidence: Confidence | None = None
    method: NewsEstimateMethod | None = None
    analogs_count: int | None = None
    positions: list[NewsPositionEstimate] = Field(default_factory=list)
    calc_id: str | None = None
    event_id: str | None = None
    as_of: UtcDatetime

    @model_validator(mode="after")
    def _figures_match_status(self) -> "NewsEstimateOut":
        figures = (
            self.impact_eur,
            self.low_eur,
            self.high_eur,
            self.impact_pct,
            self.low_pct,
            self.high_pct,
            self.horizon_sessions,
            self.confidence,
            self.method,
            self.calc_id,
            self.polarity,
        )
        if self.status in (NewsEstimateStatus.ESTIMATED, NewsEstimateStatus.MEASURED):
            if any(value is None for value in figures):
                raise ValueError(f"Una estimación `{self.status}` lleva todas sus cifras")
            assert self.low_eur is not None and self.high_eur is not None
            assert self.impact_eur is not None
            if not self.low_eur <= self.impact_eur <= self.high_eur:
                raise ValueError("Rango incoherente: low_eur ≤ impact_eur ≤ high_eur")
        elif any(value is not None for value in figures) or self.positions:
            raise ValueError(f"Una estimación `{self.status}` no lleva cifras")
        return self


class NewsItemOut(ContractModel):
    """Una noticia vista desde una cartera.

    - `summary`: resumen de la fuente (puede llevar cifras de la propia noticia).
    - `asset_ids`: posiciones de la cartera afectadas, directamente o dentro de un fondo.
    - `causal_chain` y los textos de `channels`: los redacta el agente, sin números.
    - `estimate`: `null` mientras la noticia no está clasificada.
    """

    id: str
    category: NewsCategory
    title: str
    summary: str
    published_at: UtcDatetime
    source: SourceRef
    companies: list[CompanyRef]
    asset_ids: list[str]
    channels: list[NewsChannel]
    causal_chain: list[str]
    relevance: Relevance
    estimate: NewsEstimateOut | None

    @field_validator("causal_chain")
    @classmethod
    def _chain_without_digits(cls, value: list[str]) -> list[str]:
        if any(_DIGIT.search(step) for step in value):
            raise ValueError("La cadena causal no lleva números (regla 1)")
        return value
