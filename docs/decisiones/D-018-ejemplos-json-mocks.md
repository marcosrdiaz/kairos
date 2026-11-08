### D-018 · Ejemplos JSON como fuente de los mocks
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: backend y frontend necesitan mocks coherentes con los contratos desde el domingo.
- Decisión: cada esquema tiene un JSON en `backend/app/schemas/examples/<Modelo>.json` con `"illustrative": true`. Un test en CI valida cada ejemplo contra su modelo Pydantic. Esos ejemplos son los mocks del backend (`mock.py` los carga) y del frontend (`make gen-api` los copia a `frontend/src/api/mocks/`, todos los que existan).
- Motivo: una sola fuente; el mock no puede divergir del contrato.
- Consecuencias: tareas T0-02 a T0-06.
