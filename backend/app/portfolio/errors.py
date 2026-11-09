"""Errores de dominio del gestor de cartera (mensajes para el usuario, en español)."""

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
