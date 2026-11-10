"""Importar una cartera desde CSV (T4-11). Lo expone `portfolio/service.py`.

`parse` es pura (texto → posiciones y errores); `import_portfolio` resuelve los activos contra el
catálogo, comprueba que hay precio y crea la cartera con sus lotes en una sola transacción. Si
alguna fila falla no se crea nada. Formato del CSV en `PortfolioImportRequest`.
"""

import csv
import io
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation

from app.core import clock
from app.core.db import session_scope
from app.core.errors import AppError, ErrorCode
from app.portfolio import ledger, manage, repository
from app.portfolio import quotes as pricing
from app.schemas.portfolio import PositionInitLine
from app.schemas.portfolio_manage import (
    LEGACY_PROFILE,
    ImportRowError,
    ImportRowErrorCode,
    PortfolioImportOut,
    PortfolioImportRequest,
)

REQUIRED = ("asset", "units", "avg_cost_eur")
OPTIONAL = ("acquired_at",)
MAX_DECIMALS = 8
"""Lo que guardan `NUMERIC(20,8)` las participaciones y el coste unitario de cada lote."""
LOOKUP_LIMIT = 50

Resolver = Callable[[str], str | None]
"""ISIN, ticker o id → `asset_id` del catálogo, o `None` si no existe."""


@dataclass
class ParsedCsv:
    positions: list[PositionInitLine] = field(default_factory=list)
    errors: list[ImportRowError] = field(default_factory=list)


def _error(line: int, column: str | None, code: ImportRowErrorCode, message: str) -> ImportRowError:
    return ImportRowError(line=line, field=column, code=code, message=message)


def _decimal(raw: str) -> Decimal | None:
    """Punto o coma decimal, sin separador de miles ni notación científica."""
    text = raw.strip()
    if "." in text and "," in text:
        return None
    text = text.replace(",", ".")
    if not text or any(c not in "0123456789.-" for c in text):
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    exponent = value.as_tuple().exponent
    if not value.is_finite() or (isinstance(exponent, int) and -exponent > MAX_DECIMALS):
        return None
    return value


def _date(raw: str, today: date) -> datetime | None:
    try:
        day = date.fromisoformat(raw.strip())
    except ValueError:
        return None
    if day > today:
        return None
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def _rows(text: str) -> tuple[list[str], list[tuple[int, dict[str, str]]]]:
    """Cabecera normalizada y filas no vacías con su número de línea (la cabecera es la 1)."""
    text = text.lstrip("﻿")
    lines = text.splitlines()
    header_at = next((n for n, line in enumerate(lines) if line.strip()), None)
    if header_at is None:
        return [], []
    delimiter = ";" if ";" in lines[header_at] else ","
    reader = csv.reader(io.StringIO("\n".join(lines[header_at:])), delimiter=delimiter)
    header = [h.strip().lower() for h in next(reader)]
    rows: list[tuple[int, dict[str, str]]] = []
    for offset, cells in enumerate(reader, start=2):
        if not any(c.strip() for c in cells):
            continue
        padded = cells + [""] * (len(header) - len(cells))
        values = {name: padded[i].strip() for i, name in enumerate(header)}
        rows.append((header_at + offset, values))
    return header, rows


def parse(text: str, resolve: Resolver, today: date) -> ParsedCsv:
    """Lee el CSV y devuelve las posiciones resueltas y todos los errores, fila a fila."""
    out = ParsedCsv()
    header, rows = _rows(text)
    if not header:
        out.errors.append(_error(1, None, ImportRowErrorCode.EMPTY_FILE, "El fichero está vacío."))
        return out
    missing = [c for c in REQUIRED if c not in header]
    for column in missing:
        message = f"Falta la columna «{column}» en la cabecera."
        out.errors.append(_error(1, column, ImportRowErrorCode.MISSING_COLUMN, message))
    if missing:
        return out
    if not rows:
        message = "El fichero solo tiene la cabecera: añade una fila por posición."
        out.errors.append(_error(1, None, ImportRowErrorCode.EMPTY_FILE, message))
        return out
    seen: dict[str, int] = {}
    for line, values in rows:
        _parse_row(line, values, resolve, today, seen, out)
    return out


def _parse_row(
    line: int,
    values: dict[str, str],
    resolve: Resolver,
    today: date,
    seen: dict[str, int],
    out: ParsedCsv,
) -> None:
    errors: list[ImportRowError] = []
    code = values["asset"]
    asset_id = resolve(code) if code else None
    if not code:
        errors.append(
            _error(line, "asset", ImportRowErrorCode.INVALID_VALUE, "Falta el ISIN o el ticker.")
        )
    elif asset_id is None:
        message = f"No encontramos el activo «{code}» en el catálogo. Revisa el ISIN o el ticker."
        errors.append(_error(line, "asset", ImportRowErrorCode.UNKNOWN_ASSET, message))
    elif asset_id in seen:
        message = f"El activo «{code}» ya aparece en la línea {seen[asset_id]}: usa una sola fila."
        errors.append(_error(line, "asset", ImportRowErrorCode.DUPLICATE_ASSET, message))
    else:
        seen[asset_id] = line

    units = _decimal(values["units"])
    if units is None or units <= 0:
        message = f"Participaciones no válidas («{values['units']}»): un número mayor que 0."
        errors.append(_error(line, "units", ImportRowErrorCode.INVALID_VALUE, message))
    cost = _decimal(values["avg_cost_eur"])
    if cost is None or cost < 0:
        message = (
            f"Precio medio no válido («{values['avg_cost_eur']}»): euros por participación, ≥ 0."
        )
        errors.append(_error(line, "avg_cost_eur", ImportRowErrorCode.INVALID_VALUE, message))
    raw_date = values.get("acquired_at", "")
    acquired_at = _date(raw_date, today) if raw_date else None
    if raw_date and acquired_at is None:
        message = f"Fecha no válida («{raw_date}»): AAAA-MM-DD y no posterior a hoy."
        errors.append(_error(line, "acquired_at", ImportRowErrorCode.INVALID_VALUE, message))

    if errors or asset_id is None or units is None or cost is None:
        out.errors.extend(errors)
        return
    out.positions.append(
        PositionInitLine(asset_id=asset_id, units=units, avg_cost_eur=cost, acquired_at=acquired_at)
    )


def _catalog_resolver() -> Resolver:
    """Coincidencia exacta (sin distinguir mayúsculas) con el id, el ISIN o el ticker. El
    catálogo los guarda en mayúsculas; la búsqueda por subcadena ya ignora mayúsculas."""

    def resolve(code: str) -> str | None:
        wanted = code.strip().upper()
        with session_scope() as session:
            found = repository.search_assets(session, wanted, LOOKUP_LIMIT)
        ids = {a.id for a in found if wanted in {a.id, a.isin or "", a.ticker or ""}}
        return ids.pop() if len(ids) == 1 else None

    return resolve


def import_portfolio(request: PortfolioImportRequest) -> PortfolioImportOut:
    """Valida el CSV; sin `dry_run`, crea la cartera y sus lotes (`initial`) a la vez.

    422 `VALIDATION_ERROR` con `details.rows` si alguna fila falla; 503 `PRICE_UNAVAILABLE` si
    un activo no tiene precio. En los dos casos no se crea nada."""
    now = clock.now()
    parsed = parse(request.csv, _catalog_resolver(), now.date())
    if parsed.errors:
        rows = [e.model_dump(mode="json") for e in parsed.errors]
        message = "Revisa el fichero: hay filas que no se pueden importar."
        raise AppError(ErrorCode.VALIDATION_ERROR, message, details={"rows": rows})
    pricing.quotes({p.asset_id for p in parsed.positions})  # PRICE_UNAVAILABLE antes de guardar
    if request.dry_run:
        return PortfolioImportOut(dry_run=True, portfolio=None, positions=parsed.positions)

    portfolio_id = repository.new_id("pf")
    with session_scope() as session:
        repository.upsert_portfolio(
            session,
            portfolio_id,
            request.name,
            LEGACY_PROFILE[request.risk_profile].value,
            manage.BASE_CURRENCY,
            now,
            kind=request.kind.value,
            risk_profile=request.risk_profile.value,
        )
        for line in parsed.positions:
            ledger.add_initial_lot(
                session,
                portfolio_id,
                line.asset_id,
                line.acquired_at or now,
                line.units,
                line.avg_cost_eur,
            )
        row = repository.get_portfolio(session, portfolio_id)
        assert row is not None
        summary = manage.summary(row)
    return PortfolioImportOut(dry_run=False, portfolio=summary, positions=parsed.positions)
