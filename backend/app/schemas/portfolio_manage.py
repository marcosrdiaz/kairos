"""Contratos para crear, editar, borrar e importar carteras (T4-09).

Sin login: el usuario crea tantas carteras como quiera (personal, negocio, familia…) y cada una es
independiente; nunca se suman cifras entre carteras. Los ids los genera el backend (`pf_` + hex).
Ejemplos en `schemas/examples/`. La lógica llega con T4-10 (gestión) y T4-11 (importación).
"""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, StringConstraints, model_validator

from app.schemas.common import ContractModel, PortfolioKind, Profile, RiskProfile
from app.schemas.portfolio import PortfolioSummaryOut, PositionInitLine

PortfolioName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)
]
"""Nombre visible de la cartera («Personal», «Negocio», «Hijos»). Sin espacios a los lados."""

IMPORT_CSV_MAX_CHARS = 200_000

LEGACY_PROFILE: dict[RiskProfile, Profile] = {
    RiskProfile.CONSERVADOR: Profile.CONSERVADOR,
    RiskProfile.MODERADO: Profile.MODERADO,
    RiskProfile.AGRESIVO: Profile.DINAMICO,
}
"""Valor del campo obsoleto `profile` que acompaña a cada `risk_profile` en las respuestas."""


class PortfolioCreateRequest(ContractModel):
    """`POST /portfolios` → 201 `PortfolioSummaryOut`. La cartera nace vacía: las posiciones se
    dan de alta con `POST /portfolios/{id}/positions` o se importan con `/portfolios/import`."""

    name: PortfolioName
    kind: PortfolioKind = PortfolioKind.PERSONAL
    risk_profile: RiskProfile


class PortfolioUpdateRequest(ContractModel):
    """`PATCH /portfolios/{id}` → 200 `PortfolioSummaryOut`. Solo cambia lo que se envía."""

    name: PortfolioName | None = None
    kind: PortfolioKind | None = None
    risk_profile: RiskProfile | None = None

    @model_validator(mode="after")
    def _something_to_change(self) -> Self:
        if self.name is None and self.kind is None and self.risk_profile is None:
            raise ValueError("Indica al menos un campo que cambiar: name, kind o risk_profile")
        return self


class PortfolioImportRequest(ContractModel):
    """`POST /portfolios/import`: crea una cartera a partir de un CSV.

    `csv` es el texto del fichero (el navegador lo lee y lo envía). Cabecera obligatoria y una
    fila por posición:

    - `asset`: ISIN o ticker de un activo del catálogo (`GET /assets/lookup`).
    - `units`: participaciones, > 0.
    - `avg_cost_eur`: precio medio de compra en euros, ≥ 0.
    - `acquired_at` (opcional): fecha de compra `AAAA-MM-DD`; si falta, la de hoy.

    Decimales con punto o con coma; separador de columnas `,` o `;`. Si alguna fila falla no se
    crea nada: 422 `VALIDATION_ERROR` con `details.rows` = lista de `ImportRowError`. Con
    `dry_run` solo se valida (200 y `portfolio` = `null`); sin él, 201.
    """

    name: PortfolioName
    kind: PortfolioKind = PortfolioKind.PERSONAL
    risk_profile: RiskProfile
    csv: str = Field(min_length=1, max_length=IMPORT_CSV_MAX_CHARS)
    dry_run: bool = False


class ImportRowErrorCode(StrEnum):
    EMPTY_FILE = "empty_file"
    MISSING_COLUMN = "missing_column"
    UNKNOWN_ASSET = "unknown_asset"
    DUPLICATE_ASSET = "duplicate_asset"
    INVALID_VALUE = "invalid_value"


class ImportRowError(ContractModel):
    """Un error de la importación. `line` cuenta desde 1 (la cabecera); `field` es la columna, o
    `null` si el error es de todo el fichero o de toda la fila."""

    line: int = Field(ge=1)
    field: str | None
    code: ImportRowErrorCode
    message: str


class PortfolioImportOut(ContractModel):
    """Respuesta de `POST /portfolios/import`. `positions` son las filas ya resueltas contra el
    catálogo (`asset_id` del activo), en el orden del fichero."""

    dry_run: bool
    portfolio: PortfolioSummaryOut | None
    positions: list[PositionInitLine]
