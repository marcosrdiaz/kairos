"""Escenarios ¿Y si…? (`SPEC.md` §8.3): el mismo cálculo con shocks fijados por el usuario."""

from collections.abc import Mapping, Sequence
from decimal import Decimal

from app.core.errors import AppError, ErrorCode
from app.impact.engine import ImpactResult, PositionIn, ShocksIn, compute_impact
from app.schemas.common import Factor


def estimate(
    positions: Sequence[PositionIn], factor_shocks: Mapping[Factor, Decimal], coverage: Decimal
) -> ImpactResult:
    if factor_shocks.get(Factor.EURUSD, Decimal("0")) <= Decimal("-1"):
        raise AppError(
            ErrorCode.VALIDATION_ERROR, "La variación del EUR/USD debe ser mayor que -100 %."
        )
    return compute_impact(positions, ShocksIn(factor_shocks, {}, {}), coverage)
