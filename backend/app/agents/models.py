"""Registro de llamadas a agentes (`SPEC.md` §6): depuración y métrica de latencia."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AgentLog(Base):
    __tablename__ = "agent_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent: Mapped[str] = mapped_column(String(32), index=True)
    model: Mapped[str] = mapped_column(String(64))
    prompt_hash: Mapped[str] = mapped_column(String(64))
    tool_calls: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    output: Mapped[str] = mapped_column(Text)
    guardian_verdict: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
