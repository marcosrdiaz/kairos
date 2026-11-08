"""Errores de la API (diseño del MVP §3).

Toda respuesta de error tiene la forma
`{"code": "...", "message": "texto en español", "details": {...}}`.
Los módulos lanzan `AppError(ErrorCode.X, "mensaje", details={...})`; `install_handlers` la traduce.
"""

from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INSUFFICIENT_UNITS = "INSUFFICIENT_UNITS"
    TRANSFER_NOT_ALLOWED = "TRANSFER_NOT_ALLOWED"
    PRICE_UNAVAILABLE = "PRICE_UNAVAILABLE"
    DCA_ALLOCATION_INVALID = "DCA_ALLOCATION_INVALID"
    DEMO_MODE_DISABLED = "DEMO_MODE_DISABLED"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    SENTENCE_NOT_APPROVED = "SENTENCE_NOT_APPROVED"


DEFAULT_STATUS: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.INSUFFICIENT_UNITS: 422,
    ErrorCode.TRANSFER_NOT_ALLOWED: 422,
    ErrorCode.PRICE_UNAVAILABLE: 503,
    ErrorCode.DCA_ALLOCATION_INVALID: 422,
    ErrorCode.DEMO_MODE_DISABLED: 403,
    ErrorCode.UPSTREAM_UNAVAILABLE: 503,
    ErrorCode.SENTENCE_NOT_APPROVED: 404,
}


class AppError(Exception):
    """Error de dominio con código estable y mensaje para el usuario."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details: dict[str, Any] = details or {}
        self.status_code = status_code or DEFAULT_STATUS[code]


def _body(code: ErrorCode, message: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"code": code.value, "message": message, "details": details}


async def _app_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return JSONResponse(
        status_code=exc.status_code, content=_body(exc.code, exc.message, exc.details)
    )


async def _validation_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [
        {"loc": [str(p) for p in e.get("loc", ())], "msg": str(e.get("msg", ""))}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_body(
            ErrorCode.VALIDATION_ERROR, "Los datos enviados no son válidos.", {"errors": errors}
        ),
    )


async def _http_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    if exc.status_code == 404:
        body = _body(ErrorCode.NOT_FOUND, "No encontrado.", {})
    else:
        body = _body(ErrorCode.VALIDATION_ERROR, str(exc.detail), {})
    return JSONResponse(status_code=exc.status_code, content=body)


def install_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(StarletteHTTPException, _http_handler)
