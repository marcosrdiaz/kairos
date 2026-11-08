"""Registro de todos los modelos de BD. Importarlo rellena `Base.metadata` con todas las tablas.

Lo usan `alembic/env.py` y el fixture `db` de los tests. Hay claves foráneas entre módulos, así
que las tablas se cargan todas juntas antes de crear el esquema.
Al añadir un `models.py`, regístralo aquí.
"""

from app.agents import models as agents_models
from app.alerts import models as alerts_models
from app.core import trace as core_trace
from app.events import models as events_models
from app.exposure import models as exposure_models
from app.impact import models as impact_models
from app.portfolio import models as portfolio_models
from app.prices import models as prices_models

__all__ = [
    "agents_models",
    "alerts_models",
    "core_trace",
    "events_models",
    "exposure_models",
    "impact_models",
    "portfolio_models",
    "prices_models",
]
