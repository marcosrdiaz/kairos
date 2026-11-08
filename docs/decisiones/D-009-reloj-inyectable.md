### D-009 · Reloj inyectable y replay con fecha de hoy
- Fecha: 2026-11-08 · Autor: equipo · Estado: Sustituida por D-031
- Contexto: DCA, estados de 72 h y eventos dependen de la fecha; en la demo hay que controlarla.
- Decisión: `app.core.clock.now()` en todo el backend; `DEMO_CLOCK` y `/demo/clock` la fijan. El replay reinyecta el evento con `occurred_at = now()` y calcula el impacto sobre la valoración actual, sin reescribir precios.
- Consecuencias: prohibido `datetime.now()` (regla de ruff `DTZ`).
