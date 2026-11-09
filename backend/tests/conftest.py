"""Fixtures comunes.

- Los tests no tocan Postgres ni APIs externas: `db` crea un SQLite temporal con todas las tablas
  registradas en `Base.metadata`.
- El reloj se reinicia entre tests; `DEMO_CLOCK` no se hereda del entorno.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.core import clock
from app.core.db import Base, get_engine, get_sessionmaker


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("DEMO_CLOCK", "")
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    clock.reset()
    from app.status import service as status_service

    status_service.reset()  # el estado precalculado vive en memoria, no en el SQLite del test
    yield
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    clock.reset()


@pytest.fixture
def db() -> Iterator[None]:
    """Base de datos vacía con todas las tablas.

    Sin `drop_all` al terminar: el SQLite vive en el `tmp_path` del test y se descarta entero.
    """
    import app.models  # noqa: F401  (registra todas las tablas en Base.metadata)

    Base.metadata.create_all(get_engine())
    yield


@pytest.fixture
def client(db: None) -> Iterator[TestClient]:
    """Cliente de la API sobre una BD con `data/seed` cargado (Laura y Javier, T1-03).

    Precios: los CSV reales de `data/prices` (T1-09). Para cifras fijas en un test, activa un
    `FakePriceProvider` (`tests/fakes/price_provider.py`).
    """
    from app.exposure import service as exposure_service
    from app.main import create_app
    from app.portfolio import service as portfolio_service

    portfolio_service.load_seed()
    exposure_service.load_compositions()
    with TestClient(create_app()) as test_client:
        yield test_client
