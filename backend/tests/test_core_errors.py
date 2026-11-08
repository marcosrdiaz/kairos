from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import DEFAULT_STATUS, AppError, ErrorCode, install_handlers
from app.schemas.common import ErrorOut

EXPECTED_CODES = {
    "VALIDATION_ERROR",
    "NOT_FOUND",
    "INSUFFICIENT_UNITS",
    "TRANSFER_NOT_ALLOWED",
    "PRICE_UNAVAILABLE",
    "DCA_ALLOCATION_INVALID",
    "DEMO_MODE_DISABLED",
    "UPSTREAM_UNAVAILABLE",
    "SENTENCE_NOT_APPROVED",
}


def _app() -> FastAPI:
    app = FastAPI()
    install_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise AppError(
            ErrorCode.TRANSFER_NOT_ALLOWED,
            "Los ETF no admiten traspaso sin tributar.",
            details={"from_asset_type": "etf"},
        )

    @app.get("/demo")
    def demo() -> None:
        raise AppError(ErrorCode.DEMO_MODE_DISABLED, "El modo demo está desactivado.")

    @app.get("/items/{item_id}")
    def item(item_id: int) -> dict[str, int]:
        return {"id": item_id}

    return app


def test_all_codes_from_design_exist_with_status() -> None:
    assert {c.value for c in ErrorCode} == EXPECTED_CODES
    assert set(DEFAULT_STATUS) == set(ErrorCode)


def test_app_error_returns_contract_body() -> None:
    response = TestClient(_app()).get("/boom")
    assert response.status_code == 422
    body = ErrorOut.model_validate(response.json())
    assert body.code == "TRANSFER_NOT_ALLOWED"
    assert body.details == {"from_asset_type": "etf"}


def test_demo_mode_disabled_is_403() -> None:
    response = TestClient(_app()).get("/demo")
    assert response.status_code == 403
    assert response.json()["code"] == "DEMO_MODE_DISABLED"


def test_request_validation_uses_validation_error_code() -> None:
    response = TestClient(_app()).get("/items/abc")
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    ErrorOut.model_validate(response.json())


def test_unknown_route_uses_not_found_code() -> None:
    response = TestClient(_app()).get("/nope")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
