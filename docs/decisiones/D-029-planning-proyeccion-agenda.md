### D-029 · Proyección y agenda en un módulo `planning`
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 15 del diseño; la proyección y la agenda estaban en el camino crítico del motor de impacto.
- Decisión: viven en `backend/app/planning/` (T1-14, T2-06) y llaman a `impact` y `exposure` solo vía `service.py`. Los endpoints `/projection` y `/agenda` son de ese módulo.
