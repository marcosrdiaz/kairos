"""Acceso a base de datos compartido: `Base` declarativa, engine y sesiones.

Los modelos de cada módulo heredan de `Base`. Solo `repository.py` de cada módulo abre sesiones.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _sqlite_foreign_keys(dbapi_connection: Any, _record: Any) -> None:
    """SQLite no aplica las claves foráneas (ni `ON DELETE CASCADE`) si no se le pide en cada
    conexión. Así los tests borran igual que Postgres (T4-10)."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@lru_cache
def get_engine() -> Engine:
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _sqlite_foreign_keys)
    return engine


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Sesión con commit al salir y rollback si hay excepción."""
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """Dependencia de FastAPI."""
    with session_scope() as session:
        yield session
