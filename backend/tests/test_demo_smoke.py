"""El guion de demo de punta a punta por API (`scripts/demo_smoke.py`), con datos reales y sin red.

Sin clave de Claude: el analizador usa el respaldo y el explicador, las plantillas.
"""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load_smoke() -> ModuleType:
    spec = importlib.util.spec_from_file_location("demo_smoke", SCRIPTS / "demo_smoke.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def smoke() -> ModuleType:
    return _load_smoke()


@pytest.fixture
def demo_client(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Backend con el reloj de `.env.example` y las betas calculadas, como tras `make up`."""
    monkeypatch.setenv("DEMO_CLOCK", "2026-11-06T18:00:00Z")
    get_settings.cache_clear()
    subprocess.run(
        [sys.executable, str(SCRIPTS / "compute_betas.py")],
        cwd=ROOT / "backend",
        env=os.environ.copy(),
        capture_output=True,
        check=True,
    )
    return client


def test_the_whole_script_works(demo_client: TestClient, smoke: Any) -> None:
    lines: list[str] = []

    smoke.run(demo_client, lines.append)

    assert [line.split(":")[0] for line in lines] == [f"OK  {name}" for name, _ in smoke.STEPS]


def test_reports_the_step_that_fails(smoke: Any) -> None:
    """Sin backend detrás: el primer paso falla y el error dice cuál es."""

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"code": "INTERNAL"})

    with httpx.Client(base_url="http://smoke", transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(smoke.SmokeError, match="Paso 1 Tranquilo"):
            smoke.run(client, lambda _line: None)
