### D-031 · Reloj inyectable y ajuste de demo en la valoración (sustituye a D-009)
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: DCA, estados de 72 h y eventos dependen de la fecha. Además, D-009 decía que el replay se calcula "sin reescribir precios"; el equipo decidió que en modo demo el patrimonio mostrado sí refleje el evento (decisión 17 del diseño).
- Decisión:
  - Sigue vigente de D-009: `app.core.clock.now()` en todo el backend; `DEMO_CLOCK` y `/demo/clock` la fijan; prohibido `datetime.now()` (regla de ruff `DTZ`); el replay reinyecta el evento con `occurred_at = now()` y calcula el impacto sobre la valoración actual.
  - Nuevo: **solo con `DEMO_MODE=true`**, la valoración suma el impacto central estimado de cada posición, con la etiqueta "Estimación tras el evento" y su `calc_id` (`demo_adjustments` en `PortfolioOut`). Los precios no se tocan: el ajuste va aparte y se borra en `/demo/reset`.
- Consecuencias: T2-02 implementa `apply_demo_adjustment`. `change_week_*` y `by_asset` de `explain_move` lo incluyen.
