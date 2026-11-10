"""Noticias guardadas (T4-28, `SPEC.md` §6). Solo `news/repository.py` las consulta."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class NewsItem(Base):
    """Una noticia de una fuente real, sin duplicados (`url_key` único; `title_key` para el mismo
    titular en otro medio).

    `classification` la rellena el clasificador (T4-29): categoría, empresas, canales con su
    dirección, cadena causal y relevancia, **sin cifras**. `null` mientras no está clasificada.
    """

    __tablename__ = "news_item"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    url: Mapped[str] = mapped_column(String(2000))
    url_key: Mapped[str] = mapped_column(String(64), unique=True)
    title_key: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_name: Mapped[str] = mapped_column(String(120))
    provider: Mapped[str] = mapped_column(String(16))
    language: Mapped[str] = mapped_column(String(8))
    query: Mapped[str] = mapped_column(String(300))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    classification: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    classifier_key: Mapped[str | None] = mapped_column(String(40), nullable=True)
    """Versión del prompt + modelo con que se clasificó: si cambia, se vuelve a clasificar."""
