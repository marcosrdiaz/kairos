### D-080 · Datos de la demo (T2-15): reloj, última aportación de Laura y formato de la agenda
- Fecha: 2026-11-09 · Autor: Jaime · Estado: Propuesta
- Contexto: T2-15 revisa los datos contra §5 del diseño. El paso 5 no tenía ninguna oportunidad para Laura, el reloj de demo estaba sin fijar y faltaba `agenda.json`.
- Decisión:
  - **`DEMO_CLOCK=2026-11-06T18:00:00Z`** en `.env.example`: el día del último cierre de `data/prices`. Las cifras no cambian según el día en que se ensaye y el DCA de Javier (10-nov) no vence durante la demo.
  - **`dca_laura.last_execution_at` = 2026-10-05**, y `next_execution_at` sigue en 2026-12-05. Es un estado al que se llega saltando la aportación de noviembre. Con el 2026-11-05, la agenda mostraría una aportación en el pasado.
  - **`data/events/agenda.json`**: lista `events` con `id`, `offset_days`, `time_utc`, `kind`, `title` y `factor`; en los resultados, además, `company` con la clave de empresa del look-through (`NVDA`). Es ilustrativa (`"illustrative": true`) y no lleva cifras: T2-06 calcula la exposición.
- Motivo: el guion necesita cifras repetibles y una oportunidad real, calculada por la regla `cheaper_contribution` sin tocarla.
- Alternativas descartadas: `next_execution_at` = 2026-11-05 (fecha ya pasada en la agenda); otra fecha de última aportación (no coincide con el día 5 del plan).
- Consecuencias: Laura no tiene aportación en noviembre en el seed. Quien ya tenga `.env` debe añadir `DEMO_CLOCK` a mano. Comprobado contra el motor real con betas calculadas: RV 75,98 % en Tranquilo; EE. UU. 63,6 % y 7 mayores empresas 25,7 % (el guion dice estas, no las de §5); impacto de NVIDIA −337,06 € en Laura (umbral 211,68 €) y −239,29 € en Javier; radar con `cheaper_contribution` −4,01 %; `on_track: true`.
