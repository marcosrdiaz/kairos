# Registro de decisiones — KAIROS

Sirve para retomar el trabajo tras un `/clear` o al cambiar de tarea sin repetir discusiones.

## Cómo se usa

- **Un fichero por decisión** en `docs/decisiones/`: `D-NNN-slug.md` (el ID y un slug corto del título, en minúsculas, sin tildes ni espacios). Así dos PRs que añaden decisiones no se pisan. Este fichero solo tiene la cabecera y el índice.
- **Nueva decisión:** crea `docs/decisiones/D-XXX-<slug>.md` con el ID provisional `D-XXX` (si la rama trae varias, `D-XXX-a-<slug>.md`, `D-XXX-b-<slug>.md`…). La primera línea es `### D-XXX · Título` (con el sufijo si lo hay) y la segunda, `- Fecha: … · Autor: … · Estado: …`. Usa `/decision` o la plantilla de abajo. No edites este fichero.
- **IDs correlativos `D-0xx`, asignados por la Action.** Al entrar en `main`, `renumber-decisions` (`scripts/renumber_decisions.py`) renombra tu fichero con el siguiente ID, cambia el ID dentro y en las referencias `D-XXX` de los ficheros **del mismo PR**, y regenera el índice. Fuera del PR (p. ej. en el tablero) una decisión sin mergear se cita por su título, nunca como `D-XXX`. No numeres a mano ni renumeres en el PR.
- **No se borra ni se reescribe una decisión.** Si cambia, se crea una nueva que la sustituye y en la antigua solo se cambia *Estado* a `Sustituida por D-xxx`, editando su fichero: el índice lo recoge solo. `docs/decisiones/` es una excepción a la propiedad por tarea: cualquiera puede añadir.
- **El índice de abajo se genera: no lo edites a mano.** El CI falla si un PR cambia a mano una fila de una decisión que el PR no toca. Si quieres regenerarlo en local: `python scripts/renumber_decisions.py --index-only`. Solo lista las decisiones ya numeradas.
- **Estados**: `Propuesta` (falta validar con el equipo en el siguiente checkpoint) · `Aceptada` · `Sustituida por D-xxx` · `Descartada`.
- Una decisión merece entrada si: cambia un contrato o el modelo de datos, añade una dependencia, afecta a otro módulo, o la vas a olvidar en 2 horas.
- Plantilla del fichero `docs/decisiones/D-XXX-<slug>.md`:

```
### D-XXX · Título corto   (ID provisional; la Action lo numera al entrar en main)
- Fecha: AAAA-MM-DD HH:MM · Autor: nombre · Estado: Propuesta
- Contexto: qué problema había.
- Decisión: qué se hace.
- Motivo: por qué esto y no otra cosa.
- Alternativas descartadas: ...
- Consecuencias: qué cambia, quién se ve afectado, ficheros.
```

## Índice

> **Generado: no editar a mano.** Lo regenera la Action `renumber-decisions` a partir de la fecha, el título y el estado de cada fichero de `docs/decisiones/`.

<!-- INDICE:INICIO -->
| ID | Fecha | Título | Estado |
| --- | --- | --- | --- |
| [D-001](decisiones/D-001-stack.md) | 2026-11-08 | Stack: FastAPI + React/TS + PostgreSQL + Docker Compose | Aceptada |
| [D-002](decisiones/D-002-llm-no-calcula.md) | 2026-11-08 | El LLM nunca calcula cifras | Aceptada |
| [D-003](decisiones/D-003-eventos-replay.md) | 2026-11-08 | Eventos en modo replay | Aceptada |
| [D-004](decisiones/D-004-widget-simulado.md) | 2026-11-08 | Widget simulado en web móvil, sin nativo | Aceptada |
| [D-005](decisiones/D-005-operaciones-registros.md) | 2026-11-08 | Operaciones como registros, no órdenes | Aceptada |
| [D-006](decisiones/D-006-monorepo-por-duenos.md) | 2026-11-08 | Monorepo con carpetas por dueño y `service.py` como frontera | Sustituida por D-016 |
| [D-007](decisiones/D-007-posiciones-lotes-fiscales.md) | 2026-11-08 | Posiciones derivadas de lotes fiscales | Propuesta |
| [D-008](decisiones/D-008-decimal-dinero.md) | 2026-11-08 | `Decimal` para dinero y participaciones | Propuesta |
| [D-009](decisiones/D-009-reloj-inyectable.md) | 2026-11-08 | Reloj inyectable y replay con fecha de hoy | Sustituida por D-031 |
| [D-010](decisiones/D-010-guardian-determinista.md) | 2026-11-08 | Guardián determinista, validación frase a frase | Propuesta |
| [D-011](decisiones/D-011-contexto-precargado-voz.md) | 2026-11-08 | Contexto precargado para la voz | Propuesta |
| [D-012](decisiones/D-012-modelos-proveedores-env.md) | 2026-11-08 | Modelos y proveedores configurables por `.env` | Aceptada |
| [D-013](decisiones/D-013-sin-login-selector.md) | 2026-11-08 | Sin login: selector de cartera Laura / Javier | Propuesta |
| [D-014](decisiones/D-014-datos-offline.md) | 2026-11-08 | Modo de datos `offline` por defecto | Propuesta |
| [D-015](decisiones/D-015-contratos-mocks-domingo.md) | 2026-11-08 | Contratos y mocks antes del domingo 8 a las 23:59 | Propuesta |
| [D-016](decisiones/D-016-modelo-sin-roles.md) | 2026-11-08 | Modelo de trabajo sin roles: propiedad por tarea y fases (sustituye a D-006) | Aceptada |
| [D-017](decisiones/D-017-claims-directos-main.md) | 2026-11-08 | Claims de tareas directos a `main` | Aceptada |
| [D-018](decisiones/D-018-ejemplos-json-mocks.md) | 2026-11-08 | Ejemplos JSON como fuente de los mocks | Aceptada |
| [D-019](decisiones/D-019-proveedores-llm-voz.md) | 2026-11-08 | Proveedor de LLM y voz | Aceptada |
| [D-020](decisiones/D-020-eventos-del-replay.md) | 2026-11-08 | Eventos del replay | Aceptada |
| [D-021](decisiones/D-021-consenso-solo-bce.md) | 2026-11-08 | Consenso solo para el BCE | Aceptada |
| [D-022](decisiones/D-022-umbral-desviacion-plan.md) | 2026-11-08 | Umbral de desviación del plan: `drift_threshold` = 0,10 | Aceptada |
| [D-023](decisiones/D-023-f11-f13-mvp.md) | 2026-11-08 | F11 y F13 en versión mínima pasan a MVP | Aceptada |
| [D-024](decisiones/D-024-hito-guion-completo.md) | 2026-11-08 | Hito del guion completo: martes 10 a las 18:00 | Aceptada |
| [D-025](decisiones/D-025-magnitudes-de-los-datos.md) | 2026-11-08 | Las magnitudes de un evento salen de los datos | Aceptada |
| [D-026](decisiones/D-026-precios-directo-clave.md) | 2026-11-08 | Precios en directo solo con clave de mercado | Aceptada |
| [D-027](decisiones/D-027-zip-sin-claves.md) | 2026-11-08 | El ZIP sin claves de Claude y ElevenLabs | Aceptada |
| [D-028](decisiones/D-028-paso-1-cartera-ejemplo.md) | 2026-11-08 | El paso 1 del guion carga la cartera de ejemplo | Aceptada |
| [D-029](decisiones/D-029-planning-proyeccion-agenda.md) | 2026-11-08 | Proyección y agenda en un módulo `planning` | Aceptada |
| [D-030](decisiones/D-030-anio-demo-clock.md) | 2026-11-08 | Año de `DEMO_CLOCK` | Aceptada |
| [D-031](decisiones/D-031-reloj-ajuste-demo.md) | 2026-11-08 | Reloj inyectable y ajuste de demo en la valoración (sustituye a D-009) | Aceptada |
| [D-032](decisiones/D-032-avisos-minimos-mvp.md) | 2026-11-08 | Avisos mínimos (`event_impact`, 2 por semana ISO) pasan a MVP | Aceptada |
| [D-033](decisiones/D-033-herramientas-claude-code.md) | 2026-11-08 | Herramientas de Claude Code a nivel de proyecto | Aceptada |
| [D-034](decisiones/D-034-esqueleto-t0-01.md) | 2026-11-08 | Esqueleto (T0-01): ficheros extra, servicio `seed` y `calc_trace` en `core` | Aceptada |
| [D-035](decisiones/D-035-frontend-base-t0-07.md) | 2026-11-08 | Dependencias y base del frontend (T0-07) | Aceptada |
| [D-036](decisiones/D-036-contrato-cartera-t0-02.md) | 2026-11-08 | Contrato de cartera (T0-02): peticiones, variantes de ejemplo y mock por API | Aceptada |
| [D-037](decisiones/D-037-make-gen-api-t0-03.md) | 2026-11-08 | `make gen-api` (T0-03): `openapi-typescript` por `npx` con versión fija, tipos raíz y salida en el repo | Aceptada |
| [D-038](decisiones/D-038-formato-seed-t0-08.md) | 2026-11-08 | Formato de `data/seed` y supuestos de rentabilidad (T0-08) | Propuesta |
| [D-039](decisiones/D-039-contratos-eventos-agentes-t0-05.md) | 2026-11-08 | Contratos de eventos, agentes y avisos (T0-05) | Aceptada |
| [D-040](decisiones/D-040-contrato-voz-t0-06.md) | 2026-11-08 | Contrato y mock de voz (T0-06): mensajes STT por clase, caché de frases aprobadas y `SENTENCE_NOT_APPROVED` → 404 | Aceptada |
| [D-041](decisiones/D-041-contrato-impacto-t0-04.md) | 2026-11-08 | Contrato de impacto y exposición (T0-04): rutas, modelos añadidos y ejemplos | Propuesta |
| [D-042](decisiones/D-042-modelo-datos-t1-01.md) | 2026-11-08 | Modelo de datos y migración inicial (T1-01): tablas de DCA y de ajuste de demo, columnas añadidas y registro `app.models` | Propuesta |
| [D-043](decisiones/D-043-ids-elevenlabs-t0-09.md) | 2026-11-08 | IDs de ElevenLabs (T0-09): Scribe v2 Realtime, Flash v2.5, voz en español y normalización de cifras | Propuesta |
| [D-044](decisiones/D-044-eventos-replay-texto-t0-10.md) | 2026-11-08 | Eventos de replay (T0-10): formato del texto como entrada de fuente | Propuesta |
| [D-045](decisiones/D-045-historicos-observed-t1-09.md) | 2026-11-08 | Históricos y `observed` (T1-09): series de factores, formato CSV y sesión de reacción | Propuesta |
| [D-046](decisiones/D-046-contratos-activo-precio-t1-03.md) | 2026-11-08 | Contratos de activo, precio y reset de demo (T1-03): `AssetOut`, `PriceOut`, `DemoResetRequest/Out` | Propuesta |
| [D-047](decisiones/D-047-precios-offline-t1-02.md) | 2026-11-08 | Precios offline (T1-02): lectura de `data/prices` y `data/factors/EURUSD.csv`, catálogo desde `assets.json` y precios en memoria | Propuesta |
| [D-048](decisiones/D-048-valoracion-alta-seed-t1-03.md) | 2026-11-08 | Valoración, alta y seed (T1-03): redondeo, cambio semanal, seed idempotente y `ensure_exists` para los mocks | Propuesta |
| [D-049](decisiones/D-049-composicion-fondos-t1-08.md) | 2026-11-08 | Composición de fondos y ETF (T1-08): formato del CSV, residuos por país, divisa de los fondos cubiertos y claves de empresa | Propuesta |
| [D-050](decisiones/D-050-betas-factor-t1-12.md) | 2026-11-08 | Betas de factor (T1-12): OLS multivariante con numpy, ventana de 3 años y activos sin betas | Propuesta |
| [D-051](decisiones/D-051-motor-impacto-t1-13.md) | 2026-11-08 | Motor de impacto (T1-13): rango, efecto dólar, persistencia y lecturas de otros módulos | Propuesta |
| [D-052](decisiones/D-052-look-through-t1-11.md) | 2026-11-08 | Look-through (T1-11): carga de `composition`, posiciones sin composición, cobertura y listas devueltas | Propuesta |
| [D-053](decisiones/D-053-pipeline-replay-t1-15.md) | 2026-11-08 | Pipeline de replay (T1-15): SDK de Anthropic, filtro provisional, fechas y reset | Propuesta |
| [D-054](decisiones/D-054-compraventa-fifo-t1-04.md) | 2026-11-09 | Compra y venta FIFO (T1-04): redondeos, plusvalía, operaciones por importe y reparto de `portfolio/` en submódulos | Propuesta |
| [D-055](decisiones/D-055-contrato-ejecuciones-dca-t1-06.md) | 2026-11-09 | Contrato de las ejecuciones DCA (T1-06): listar las aportaciones de una cartera y respuesta de `/demo/dca/run` | Propuesta |
| [D-056](decisiones/D-056-dca-real-t1-06.md) | 2026-11-09 | DCA real (T1-06): calendario, reparto en céntimos, ejecución forzada en demo y precio al confirmar | Propuesta |
| [D-057](decisiones/D-057-plan-variacion-valor-t1-07.md) | 2026-11-09 | Plan y variación de valor (T1-07): asignación actual con `mixed`, desviación, `PUT /plan` y `get_value_change` | Propuesta |
| [D-058](decisiones/D-058-guardian-reglas-cifras-forma.md) | 2026-11-09 | Guardián (T1-16): cómo casa cifras, qué patrones bloquea y cuándo aplica la forma | Propuesta |
| [D-059](decisiones/D-059-app-adaptable-escritorio-t1-18.md) | 2026-11-09 | App adaptable a escritorio y tarjeta de estado en Inicio (T1-18) | Propuesta |
| [D-060](decisiones/D-060-tema-claro-oscuro-t1-22.md) | 2026-11-09 | Tema claro/oscuro, tokens `--kairos-color-*` y estilo visual en oro (T1-22) | Propuesta |
| [D-061](decisiones/D-061-carrusel-noticias-t2-19.md) | 2026-11-09 | Carrusel de noticias en Inicio: datos, ilustraciones y accesibilidad (T2-19) | Propuesta |
<!-- INDICE:FIN -->
