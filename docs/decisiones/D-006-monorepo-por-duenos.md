### D-006 · Monorepo con carpetas por dueño y `service.py` como frontera
- Fecha: 2026-11-08 · Autor: equipo · Estado: Sustituida por D-016
- Contexto: 5 personas con 5 sesiones de Claude Code en paralelo; riesgo alto de conflictos y de que una IA "arregle" el módulo de otro.
- Decisión: cada carpeta tiene dueño (`TABLERO.md`); los módulos se importan solo vía `service.py`; `schemas/` es contrato compartido y se cambia con PR propio.
- Alternativas descartadas: repos separados (más fricción con Compose y tipos compartidos).
- Consecuencias: CLAUDE.md prohíbe editar carpetas ajenas.
