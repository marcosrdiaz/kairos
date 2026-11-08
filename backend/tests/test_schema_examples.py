"""Valida todos los ejemplos de `app/schemas/examples/` contra su modelo de `app/schemas/`.

El modelo se busca por nombre (`PortfolioOut.javier.json` → `PortfolioOut`) en todos los módulos de
`app.schemas`, así que los ejemplos de cualquier tarea quedan cubiertos sin tocar este test.
"""

import importlib
import pkgutil
from pathlib import Path

import pytest

import app.schemas as schemas_package
from app.schemas.common import ContractModel
from app.schemas.examples import ILLUSTRATIVE_KEY, example_files, load, load_raw, model_name


def _contract_models() -> dict[str, type[ContractModel]]:
    found: dict[str, type[ContractModel]] = {}
    for info in pkgutil.iter_modules(schemas_package.__path__):
        module = importlib.import_module(f"app.schemas.{info.name}")
        for attr in vars(module).values():
            if (
                isinstance(attr, type)
                and issubclass(attr, ContractModel)
                and attr.__module__ == module.__name__
            ):
                found[attr.__name__] = attr
    return found


MODELS = _contract_models()
FILES = example_files()


def test_there_are_examples() -> None:
    assert FILES


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_example_is_marked_illustrative(path: Path) -> None:
    data = load_raw(path.stem)
    assert isinstance(data, dict)
    assert data.get(ILLUSTRATIVE_KEY) is True


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_example_validates_and_round_trips(path: Path) -> None:
    name = model_name(path)
    assert name in MODELS, f"No hay modelo `{name}` en app/schemas/ para {path.name}"
    data = load(path.stem)
    model = MODELS[name].model_validate(data)
    # Los ejemplos van en la forma canónica del contrato (precisión de importes, fechas en Z...).
    # Las respuestas van completas, como las emite la API; las peticiones pueden omitir opcionales.
    partial = name.endswith("Request")
    assert model.model_dump(mode="json", exclude_unset=partial) == data


PORTFOLIO_EXAMPLES = [
    "PortfolioOut",
    "PortfolioOut.javier",
    "PortfolioSummaryOut",
    "PositionsInitRequest",
    "PlanOut",
    "PlanUpdateRequest",
    "TransactionRequest",
    "TransactionRequest.sell",
    "TransactionOut",
    "TransactionOut.transfer",
    "TransferRequest",
    "ErrorOut.transfer_not_allowed",
    "DcaPlanOut",
    "DcaPlanCreateRequest",
    "DcaPlanUpdateRequest",
    "DcaExecutionOut",
    "DcaExecutionActionRequest",
    "ValueChangeOut",
    "TraceOut",
    "AssetOut",
    "PriceOut",
    "DemoResetRequest",
    "DemoResetOut",
]


@pytest.mark.parametrize("name", PORTFOLIO_EXAMPLES)
def test_portfolio_contract_has_example(name: str) -> None:
    assert any(p.stem == name for p in FILES), f"Falta schemas/examples/{name}.json"
