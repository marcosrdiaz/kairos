"""Errores de dominio del gestor de cartera (mensajes para el usuario, en español)."""

from datetime import datetime
from decimal import Decimal

from app.core.errors import AppError, ErrorCode


def portfolio_not_found(portfolio_id: str) -> AppError:
    return AppError(
        ErrorCode.NOT_FOUND,
        f"No existe la cartera «{portfolio_id}».",
        details={"portfolio_id": portfolio_id},
    )


def unknown_asset(asset_id: str) -> AppError:
    return AppError(
        ErrorCode.NOT_FOUND,
        f"No conocemos el activo «{asset_id}».",
        details={"asset_id": asset_id},
    )


def insufficient_units(asset_id: str, requested: Decimal, available: Decimal) -> AppError:
    """422 `INSUFFICIENT_UNITS`: se venden más participaciones de las que hay."""
    return AppError(
        ErrorCode.INSUFFICIENT_UNITS,
        f"Solo tienes {available.normalize():f} participaciones de este activo.",
        details={
            "asset_id": asset_id,
            "requested_units": str(requested),
            "available_units": str(available),
        },
    )


def dca_allocation_invalid(reason: str) -> AppError:
    """422 `DCA_ALLOCATION_INVALID`: el reparto no suma 1, repite activos o tiene pesos ≤ 0."""
    return AppError(
        ErrorCode.DCA_ALLOCATION_INVALID,
        f"El reparto del plan no es válido: {reason}.",
        details={"reason": reason},
    )


def dca_invalid_day(reason: str) -> AppError:
    return AppError(
        ErrorCode.VALIDATION_ERROR,
        f"El día del plan no es válido: {reason}.",
        details={"reason": reason},
    )


def dca_plan_not_found(portfolio_id: str, plan_id: str) -> AppError:
    return AppError(
        ErrorCode.NOT_FOUND,
        f"La cartera «{portfolio_id}» no tiene el plan de aportaciones «{plan_id}».",
        details={"portfolio_id": portfolio_id, "plan_id": plan_id},
    )


def dca_execution_not_found(execution_id: str) -> AppError:
    return AppError(
        ErrorCode.NOT_FOUND,
        f"No existe la aportación «{execution_id}».",
        details={"execution_id": execution_id},
    )


def plan_not_found(portfolio_id: str) -> AppError:
    return AppError(
        ErrorCode.NOT_FOUND,
        "Esta cartera aún no tiene un plan de inversión.",
        details={"portfolio_id": portfolio_id},
    )


def plan_invalid(reason: str) -> AppError:
    """422: el objetivo no suma 1 o el umbral está fuera de rango."""
    return AppError(ErrorCode.VALIDATION_ERROR, reason, details={"field": "target"})


def invalid_window(start: datetime, end: datetime) -> AppError:
    return AppError(
        ErrorCode.VALIDATION_ERROR,
        "El inicio del periodo debe ser anterior al final.",
        details={"start": start.isoformat(), "end": end.isoformat()},
    )


def price_unavailable_at(asset_id: str, at: datetime) -> AppError:
    return AppError(
        ErrorCode.PRICE_UNAVAILABLE,
        "No hay precio de este activo para esa fecha.",
        details={"asset_id": asset_id, "at": at.isoformat()},
    )


def dca_execution_resolved(execution_id: str, status: str) -> AppError:
    """422: la aportación ya se confirmó o se saltó."""
    label = "confirmada" if status == "confirmed" else "saltada"
    return AppError(
        ErrorCode.VALIDATION_ERROR,
        f"Esta aportación ya está {label}.",
        details={"execution_id": execution_id, "status": status},
    )
