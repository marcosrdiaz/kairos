"""Crea la app y monta todos los routers de `app/api/` bajo `/api/v1`.

Cada módulo de `app/api/` expone una variable `router` (`fastapi.APIRouter`). No hace falta
tocar este fichero para añadir uno: basta con crear el módulo.
"""

import importlib
import pkgutil

from fastapi import APIRouter, FastAPI

from app import api as api_package
from app.config import get_settings
from app.core.errors import install_handlers

API_PREFIX = "/api/v1"


def discover_routers() -> list[tuple[str, APIRouter]]:
    found: list[tuple[str, APIRouter]] = []
    for info in sorted(pkgutil.iter_modules(api_package.__path__), key=lambda m: m.name):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"app.api.{info.name}")
        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            found.append((info.name, router))
    return found


def create_app() -> FastAPI:
    get_settings()  # una configuración inválida (DEMO_MODE=false con offline) para el arranque
    application = FastAPI(
        title="KAIROS API",
        version="0.1.0",
        description="Contexto, no órdenes: impacto en euros de los eventos sobre tu cartera.",
    )
    install_handlers(application)
    for _, router in discover_routers():
        application.include_router(router, prefix=API_PREFIX)
    return application


app = create_app()
