### D-001 · Stack: FastAPI + React/TS + PostgreSQL + Docker Compose
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: 4 días, 5 personas, el jurado debe poder ejecutarlo.
- Decisión: backend Python 3.12 + FastAPI; frontend React + TypeScript + Vite; PostgreSQL 16; Docker Compose. Gestores `uv` y `npm`.
- Motivo: Python para pandas/statsmodels y SDKs de Anthropic y ElevenLabs; React para una web móvil que simula el widget; Compose para `docker compose up`.
- Alternativas descartadas: SQLite (menos fiel a la arquitectura del pitch, pero más simple; se puede recuperar si Postgres da guerra); app nativa.
- Consecuencias: ver `SPEC.md` §2.
