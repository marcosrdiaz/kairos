# Tablero del equipo — KAIROS

Documento vivo: qué tareas hay, quién ha cogido cada una, en qué estado está y qué bloquea a quién. Lo leen y escriben las personas y sus sesiones de Claude Code.

**Plazo:** domingo 8 de noviembre (tarde) → **miércoles 11 de noviembre a las 23:59** (cierre del formulario de BEST UC3M). Entrega interna antes de las 21:00.

## Reglas

- **No hay roles ni carpetas con dueño.** Somos 5 (Manu, Jaime, Marcos, Alons y Javi) y cualquiera puede coger cualquier tarea.
- **Coger una tarea** = commit de claim en este fichero **antes de empezar**: pon tu nombre en *Cogida por* y el estado en `🔄 en curso`. Si ya está cogida, elige otra. Usa `/coger <ID>`.
- **Propiedad por tarea.** Mientras una tarea está en curso, quien la tiene es dueño de los ficheros de su columna *Ficheros que toca*. Otra sesión no los edita: si necesita algo de ellos, apunta un bloqueo (§ Bloqueos). Por eso no se coge una tarea cuyos ficheros solapen con los de otra en curso.
- **Dependencias.** Si una tarea depende de otra, se hace antes la dependencia. `(b)` = dependencia blanda: se puede empezar con mocks o datos de prueba.
- **Fases.** Una fase está **cerrada** cuando todas sus tareas están en `main` con `make lint && make test` en verde. Se puede **adelantar** una tarea de la fase siguiente solo si todas sus dependencias están hechas.
- **Excepciones a la propiedad por tarea:** `docs/decisiones.md` (solo se añade al final) y tu propia fila de este tablero.
- **El tablero solo se modifica con commits directos a `main`** (excepción a "todo por PR"), nunca dentro de un PR, y el commit toca únicamente `docs/TABLERO.md`. Mensaje `docs: claim|release|done|block|note T<x>-<nn>`: `claim`, `release` y `done` cambian la fila de la tarea; `block` apunta o cierra una fila de *Bloqueos* (y marca `⛔`); `note` actualiza *Notas para retomar* o *Peticiones de contrato* (y marca `🧪 en PR`). Flujo: `git pull --rebase` → comprobar (p. ej. que la tarea sigue libre) → commit → `git push` justo después. Si el push falla, se repite desde el pull. Excepción puntual: `docs: tablero rules` para cambios de reglas de este propio tablero. Todo lo demás va por PR: el merge lo hace quien abre el PR, tras la aprobación de un revisor y con el CI en verde.
- **Estados:** `⬜ pendiente` · `🔄 en curso` · `🧪 en PR` · `✅ hecho` · `⛔ bloqueado`. Marcar `✅ hecho` (`docs: done T<x>-<nn>`) solo con la tarea en `main`.
- Al cerrar cada sesión (`/cierre`), actualiza *Notas para retomar* de tu tarea con un commit directo a `main` (`docs: note T<x>-<nn>`).

---

## 1. Checkpoints

Propuesta; ajustad a vuestros horarios de lunes a miércoles.

| Cuándo | Duración | Qué |
| --- | --- | --- |
| Cada mañana (antes de las 10:00) | Asíncrono | Cada uno deja su tarea en curso al día |
| Cada día, 21:30 | 15 min (llamada) | Demo desde `main`, bloqueos, validar decisiones `Propuesta` |
| Domingo 8, al acabar el reparto | 20 min | Kick-off: quién coge qué de la fase 0 |
| **Martes 10, 18:00** | 30 min | Se comprueba el guion completo y el equipo decide qué "Si da tiempo" entra; se apunta en `decisiones.md` |

## 2. Hitos

| Cuándo | Hito | Estado |
| --- | --- | --- |
| **Dom 8 · 23:59** | **Fase 0 cerrada**: esqueleto del repo en `main`, contratos y mocks publicados, datos de ejemplo empezados | ⬜ |
| **Lun 9** | **Fase 1 cerrada**: datos y motores contra el backend real. Look-through y eventos, antes de las 14:00 | ⬜ |
| **Mar 10 · 18:00** | **El guion de demo funciona entero** en `main` (fase 2 cerrada). Decisión sobre "Si da tiempo" | ⬜ |
| **Mié 11 · 16:00** | **Congelación** (solo arreglos) | ⬜ |
| **Mié 11 · 21:00** | **Entrega** (ZIP de `main` + formulario BEST UC3M); 3 h de margen sobre el cierre | ⬜ |

**Regla de recorte:** si el martes a las 15:00 el guion no va, se recorta en este orden: agenda; radar (solo `currency` y `cheaper_contribution`); operaciones en la UI (solo comprar). Voz, widget y motor de impacto no se recortan.

## 3. Pool de tareas

Definición completa en `docs/superpowers/specs/2026-11-08-kairos-mvp-design.md` §6. Formato de ID: `T<fase>-<nn>`. Añade tareas al final de su fase; no renumeres.

### Fase 0 · Cimientos y contratos (hasta el dom 8, 23:59)

| ID | Tarea | Criterio de hecho | Depende de | Ficheros que toca | Cogida por | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| T0-01 | Esqueleto: Compose (db, backend, frontend, seed), Makefile, `config.py`, `core/{clock,db,errors,trace}.py`, CI. Incluye lo común de los contratos: `schemas/common.py` (Money, SourceRef, enums compartidos, ErrorOut) y los códigos de error de `core/errors.py` | `make up` y `make test` en limpio; `main.py` monta solo todos los routers de `api/`; `common.py` y `errors.py` publicados | — | `Makefile`, `docker-compose.yml`, `.env.example`, `.gitignore`, `.github/workflows/ci.yml`, `backend/pyproject.toml`, `backend/app/{main,config}.py`, `backend/app/core/`, `backend/app/schemas/common.py`, `backend/tests/conftest.py`, `frontend/Dockerfile` (mínimo: nginx sirviendo el build de Vite) | Alons | ✅ hecho |
| T0-02 | Esquemas de cartera (§4.1) + `examples/` + `portfolio/mock.py` + test que valida todos los ejemplos | Ejemplos validan; el mock sirve `/portfolios/laura` | T0-01 | `backend/app/schemas/portfolio.py`, `backend/app/schemas/examples/` (cartera, plan, operaciones, DCA, traza), `backend/app/portfolio/{mock,service}.py`, `backend/app/api/portfolio.py`, `backend/tests/test_schema_examples.py` | Alons | ✅ hecho |
| T0-03 | `make gen-api` genera los tipos TS y copia a `frontend/src/api/mocks/` todos los `schemas/examples/*.json` que existan | El frontend importa los mocks; funciona aunque falten esquemas de otros | T0-02 | `Makefile` (solo el objetivo `gen-api`), `scripts/gen_api.py`, `frontend/src/api/generated/`, `frontend/src/api/mocks/` | Alons | ✅ hecho |
| T0-04 | Esquemas §4.3 (impacto, exposición, radar, estado, proyección, agenda, move, escenario) + ejemplos + mocks | Ejemplos validan; los endpoints responden con mock | T0-01 | `backend/app/schemas/{impact,exposure,radar,status,planning}.py`, `backend/app/schemas/examples/` (esos modelos), `backend/app/{exposure,impact,status,planning}/{mock,service}.py`, `backend/app/api/{exposure,impact,status,planning}.py` | Jaime | 🔄 en curso |
| T0-05 | Esquemas §4.2 y §4.4 (`EventAnalysis`, `ShockSet`, Ask SSE, Guardián, `ExplainerContext`, `AlertOut`) + ejemplos + mocks; el `/ask` mock emite SSE de ejemplo | El frontend recibe el SSE mock | T0-01 | `backend/app/schemas/{events,agents,alerts}.py`, `backend/app/schemas/examples/` (esos modelos), `backend/app/{agents,events,alerts}/{mock,service}.py`, `backend/app/api/{ask,events,alerts}.py`, `backend/app/{agents,events,alerts}/__init__.py`, `backend/tests/test_event_agent_examples.py` | Marcos | ✅ hecho |
| T0-06 | Contrato de voz §4.5 + mock (`/voice/tts` devuelve un mp3 fijo) | El frontend reproduce el mp3 mock | T0-01 | `backend/app/schemas/voice.py`, `backend/app/schemas/examples/` (voz), `backend/app/voice/{mock,service}.py`, `backend/app/api/voice.py`, `data/voice/mock.mp3` | Alons | ✅ hecho |
| T0-07 | Vite + TS + Tailwind + TanStack Query; 3 pestañas (Inicio · Cartera · Pregunta) y ruta `/panel` vacía. El enganche a los mocks espera a T0-03 | Navega sobre mocks | T0-03 (b) | `frontend/` salvo `Dockerfile`, `src/voice/`, `src/api/{generated,mocks}/`; `PRODUCT.md`, `DESIGN.md` | Marcos | ✅ hecho |
| T0-08 | `assets.json`, `laura.json` / `javier.json` con plan y DCA según §5, y `assumptions.json` (rentabilidad por clase de activo, con fuente y `"illustrative": true`) | Cumple la fila 1 de §5; `assumptions.json` listo para la proyección | — | `data/seed/assets.json`, `data/seed/portfolios/`, `data/seed/assumptions.json` | Jaime | ✅ hecho |
| T0-09 | Verificar IDs de Scribe v2 Realtime y Flash v2.5, y la voz en español; medir latencia | Anotado en `decisiones.md` | — | `docs/decisiones.md` (solo añadir) | Marcos | 🧪 en PR |
| T0-10 | Confirmar los 3 eventos (decisión 5 de §8) y redactar `title`, `text`, `source_urls`, `consensus`, `fallback_chain` | JSON sin `observed` todavía. Límite: lunes 14:00 | — | `data/events/replay/*.json` | Manu | 🔄 en curso |

### Fase 1 · Datos y motores (lun 9)

| ID | Tarea | Criterio de hecho | Depende de | Ficheros que toca | Cogida por | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| T1-01 | Modelos + migración (`SPEC.md` §6) | `alembic upgrade head` | T0-01 | `backend/alembic/`, `backend/app/{portfolio,prices,exposure,impact,events,alerts,agents}/models.py` | Alons | 🧪 en PR |
| T1-02 | `prices`: proveedor offline (CSV) + FX + `latest()` + `history()` | RF-03. Con CSV de prueba hasta que T1-09 esté | T1-01, T1-09 (b) | `backend/app/prices/`, `backend/tests/fakes/price_provider.py` | — | ⬜ |
| T1-03 | Alta de posiciones + seed + `/demo/reset` + `/assets/lookup` | RF-01, RF-02 | T1-01, T0-08 | `backend/app/portfolio/{service,repository,engine}.py`, `backend/app/api/{portfolio,demo,assets}.py`, `scripts/seed_db.py`, `backend/tests/golden/portfolio_init*` | — | ⬜ |
| T1-04 | Compra/venta FIFO con casos dorados | RF-04, RF-05 | T1-03 | `backend/app/portfolio/{service,repository,engine,lots}.py`, `backend/tests/golden/portfolio_fifo*` | — | ⬜ |
| T1-05 | Traspaso fondo → fondo + error con alternativa | RF-06 | T1-04 | `backend/app/portfolio/{service,transfers}.py`, `backend/tests/test_transfers.py` | — | ⬜ |
| T1-06 | DCA (planes, ejecución pendiente, confirmar/saltar, `/demo/dca/run`) | RF-07. Límite: martes 10:00 | T1-04 | `backend/app/portfolio/{service,dca}.py`, `backend/app/api/dca.py`, `backend/tests/test_dca.py` | — | ⬜ |
| T1-07 | `/plan` + `get_value_change` | RF-22 (datos) | T1-03 | `backend/app/portfolio/{service,plan}.py`, `backend/app/api/plan.py`, `backend/tests/test_plan.py` | — | ⬜ |
| T1-08 | Composición de los fondos/ETF de Laura y Javier (top-N + "Otros", `as_of`, fuente) | CSV completos; ≥ 90 % de cobertura en Laura. Límite: lunes 14:00 | — | `data/seed/compositions/` | — | ⬜ |
| T1-09 | Históricos diarios de 2–3 años (activos y factores) + `observed` de los 3 eventos calculado de esos datos | `data/prices`, `data/factors`, replay completo | T0-10 | `data/prices/`, `data/factors/`, `data/events/replay/*.json` (solo `observed`), `scripts/fetch_prices.py` | — | ⬜ |
| T1-10 | Casos dorados Laura/Javier (exposición, 3 eventos, proyección) en hoja | Revisado por otra persona | T0-08, T1-08 | `backend/tests/golden/{exposure,impact,projection}*` | — | ⬜ |
| T1-11 | Look-through, solapamientos y `radiography` | RF-08, RF-09. Límite: lunes 14:00 | T1-08 | `backend/app/exposure/{service,engine,repository}.py`, `backend/app/api/exposure.py`, `backend/tests/test_exposure*.py` | — | ⬜ |
| T1-12 | `compute_betas.py` + `factor_beta` | Betas con R², error estándar y n | T1-09, T1-01 | `scripts/compute_betas.py`, `backend/app/impact/{betas,repository}.py` | — | ⬜ |
| T1-13 | Motor de impacto: mercado, divisa, resultados, rango, confianza, polaridad; `estimate_scenario` comparte núcleo | RF-10 + dorados | T1-12 | `backend/app/impact/{service,engine,scenario}.py`, `backend/app/api/impact.py`, `backend/tests/test_impact*.py` | — | ⬜ |
| T1-14 | Proyección con DCA (`ProjectionOut`) en `planning/` | Dorado de Laura `on_track: true` | T1-07, T0-08 | `backend/app/planning/{service,projection}.py`, `backend/app/api/planning.py`, `backend/tests/test_projection.py` | — | ⬜ |
| T1-15 | Analizador + `build_shockset` + pipeline de §2 + `/demo/replay` (impacto con mock al principio) | RF-11, RF-12; fallback probado | T0-10 | `backend/app/agents/{analyzer,service}.py`, `backend/app/agents/prompts/analyzer.md`, `backend/app/events/`, `backend/app/api/events.py`, `scripts/replay_event.py` | — | ⬜ |
| T1-16 | Guardián: patrones, cifras, forma; un test por patrón y por formato de número | RF-16 | T0-05 | `backend/app/agents/guardian.py`, `backend/app/agents/prompts/forbidden.yaml`, `backend/tests/test_guardian*.py`, `backend/tests/fakes/` | — | ⬜ |
| T1-17 | Explicador: contexto precargado + herramientas + `/ask` SSE + reintento + plantilla | 3 preguntas tipo responden con FakeClaude y con Claude real | T1-16 | `backend/app/agents/{explainer,tools,context,service}.py`, `backend/app/agents/prompts/explainer.md`, `backend/app/api/ask.py` | — | ⬜ |
| T1-18 | Pantalla de inicio simulada con widget (3 estados, color + palabra) | RF-13 visual | T0-07 | `frontend/src/widget/` | — | ⬜ |
| T1-19 | Alta de cartera + selector Laura/Javier (`?p=`) | RF-01, RF-02 | T0-07 | `frontend/src/app/onboarding/`, `frontend/src/app/portfolio-picker/` | — | ⬜ |
| T1-20 | Operaciones (compra, venta, traspaso con error explicado) y DCA | RF-04–07 en UI | T0-07 | `frontend/src/app/operations/`, `frontend/src/app/dca/` | — | ⬜ |
| T1-21 | `voice/` backend: STT por WS, TTS de frases aprobadas, disclaimer | Audio de ida y vuelta con frase fija | T0-06, T0-09 | `backend/app/voice/`, `backend/app/api/voice.py`, `data/voice/disclaimer.mp3` | — | ⬜ |

### Fase 2 · Experiencia e integración (hasta el mar 10, 18:00)

| ID | Tarea | Criterio de hecho | Depende de | Ficheros que toca | Cogida por | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| T2-01 | `/traces/{calc_id}` con `parent_calc_ids` | RF-19 | T1-01 | `backend/app/core/trace.py`, `backend/app/api/traces.py` | — | ⬜ |
| T2-02 | Ajuste de demo: `portfolio.service.apply_demo_adjustment(...)` (lo llama `events` tras el impacto) + `demo_adjustments` en la valoración + borrado en `/demo/reset` | Tras el replay, `/portfolios/laura` y `/status` reflejan el impacto con etiqueta y traza | T1-03, T1-13 | `backend/app/portfolio/{service,repository,engine}.py`, `backend/app/api/demo.py` | — | ⬜ |
| T2-03 | Integración: quitar mocks del backend módulo a módulo; `/demo/clock`; smoke del guion por API | Smoke en verde (`scripts/demo_smoke.py`) | Todas las de la fase 1 | `backend/app/*/mock.py` (borrar), `backend/app/api/demo.py`, `scripts/demo_smoke.py` | — | ⬜ |
| T2-04 | `status` precalculado + `recompute` + frase vía `agents.write_status_sentence` | RF-13; `/status` < 200 ms | T1-13, T1-17 | `backend/app/status/`, `backend/app/api/status.py` | — | ⬜ |
| T2-05 | Radar (6 reglas, plantillas, invariante de oportunidad) | RF-18 | T1-11, T1-06 | `backend/app/exposure/{radar,templates}.py`, `backend/app/api/radar.py`, `backend/tests/test_radar*.py` | — | ⬜ |
| T2-06 | Agenda (`agenda.json` + DCA + exposición por factor) | Bloque del panel con datos | T1-12, T2-15 | `backend/app/planning/agenda.py`, `backend/app/api/agenda.py`, `backend/tests/test_agenda.py` | — | ⬜ |
| T2-07 | `explain_move` | "¿Por qué ha bajado?" con dato real | T1-07, T1-13 | `backend/app/impact/move.py`, `backend/app/api/move.py`, `backend/tests/test_move.py` | — | ⬜ |
| T2-08 | Avisos: score, umbral, límite semanal, mensaje validado | RF-23 (`kind=event_impact` es MVP porque lo usa el paso 3) | T1-13 | `backend/app/alerts/`, `backend/app/api/alerts.py` | — | ⬜ |
| T2-09 | Explicaciones de evento por cartera + invalidación del contexto precargado | `explanation_status: ok` en los 3 eventos × 2 carteras | T1-15, T1-13 | `backend/app/events/pipeline.py`, `backend/app/agents/context.py` | — | ⬜ |
| T2-10 | Panel: resumen, eventos (cadena, €, rango, confianza, filtro), exposición, radar, agenda | RF-17 | T0-04, T0-07 | `frontend/src/panel/` | — | ⬜ |
| T2-11 | "¿De dónde sale?" → traza desde cualquier cifra | RF-19 | T2-01 | `frontend/src/components/trace/` | — | ⬜ |
| T2-12 | Avisos de IA y "no es asesoramiento"; accesibilidad | RF-20, RNF-11 | T0-07 | `frontend/src/components/notices/`, `frontend/src/index.css` | — | ⬜ |
| T2-13 | Polling de `/status` y `/alerts` cada 5 s; aviso en pantalla de inicio (paso 3) | El widget cambia solo tras un replay | T2-04, T2-08 | `frontend/src/api/hooks/`, `frontend/src/widget/` | — | ⬜ |
| T2-14 | `src/voice/`: push-to-talk, cola de audio por frase, disclaimer, plan B de preguntas sugeridas | RF-14 de punta a punta | T1-21, T1-17 | `frontend/src/voice/` | — | ⬜ |
| T2-15 | `agenda.json`, `DEMO_CLOCK` y revisión de los datos contra §5 | Las 5 filas de §5 se cumplen | T1-11, T1-13 | `data/events/agenda.json`, `data/seed/portfolios/` | — | ⬜ |
| T2-16 | Medir latencia de voz (10 intentos) | 8/10 por debajo de 2 s o, si no, cambiar de modelo (decisión 4) | T2-14 | `scripts/measure_voice.py`, `docs/decisiones.md` (solo añadir) | — | ⬜ |

### Fase 3 · Endurecer y entregar (mar 10, 18:00 → mié 11, 21:00)

| ID | Tarea | Criterio de hecho | Depende de | Ficheros que toca | Cogida por | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| T3-01 | Evaluación de 30 preguntas (10 por tipo + 10 trampa "¿vendo?") | 0 órdenes de compraventa; tasa de bloqueo anotada | T1-17 | `scripts/eval_answers.py`, `backend/tests/eval/` | — | ⬜ |
| T3-02 | Playwright del guion de demo | E2E en verde en offline con fakes | T2-03, T2-10 | `frontend/e2e/`, `frontend/playwright.config.ts` | — | ⬜ |
| T3-03 | Escenarios ¿Y si…? en el panel (si a las 18:00 estaba en verde) | RF-21, < 500 ms | T1-13, T2-10 | `backend/app/impact/scenario.py`, `frontend/src/panel/scenarios/` | — | ⬜ |
| T3-04 | Calibrar umbrales con datos reales (estado, avisos, confianza) | Guion estable 3 veces seguidas | T2-03 | `backend/app/{status,alerts,impact}/config.py` | — | ⬜ |
| T3-05 | Prueba en máquina limpia con el ZIP | `docker compose up` + README sin ayuda | T3-06 | `docker-compose.yml`, `Makefile` (solo arreglos) | — | ⬜ |
| T3-06 | README (instalación, `.env`, ejecución, prueba) | Otra persona lo ejecuta sin ayuda | T2-03 | `README.md` | — | ⬜ |
| T3-07 | PDF de una cara + PPT + diapositiva de arquitectura | Revisado por el equipo | T2-03 | `docs/entrega/` | — | ⬜ |
| T3-08 | Vídeo de respaldo + ZIP + formulario BEST UC3M | Enviado antes de las 21:00 | T3-05, T3-07 | `docs/entrega/` | — | ⬜ |
| T3-09 | 3 ensayos cronometrados del guion | < 3 min cada uno | T2-03 | Ninguno | — | ⬜ |

## 4. Notas para retomar

Una subsección por tarea en curso. Bórrala al marcar la tarea como hecha. Plantilla:

```
### T<x>-<nn> · <nombre> — <quién>
**Qué estaba haciendo:** …
**Siguiente paso exacto:** …
**Ficheros tocados:** …
```

### T0-09 · IDs de voz de ElevenLabs — Marcos
**Estado:** PR #16 abierto (`t0-09/elevenlabs-ids`): IDs, voz (Ciro), latencia y pronunciación en `docs/decisiones.md` (entrada «IDs de ElevenLabs (T0-09)»), y los tres IDs en `.env.example`.
**Siguiente paso exacto:** que un revisor lo mire y se haga merge. La voz Ciro la eligió el equipo a oído; Carolina y Lydia quedan descartadas.
**Ficheros tocados:** `docs/decisiones.md`, `.env.example` (este último no estaba en la fila de la tarea: solo se rellenan los IDs).

### T1-21 · `voice/` backend: requisitos que deja T0-09 — Marcos (para quien coja la tarea)
**Normalizar cifras antes del TTS:** Flash v2.5 no normaliza texto y lee mal las cifras largas ("42.380 euros" salió distinto en cada repetición). `voice/` debe convertir las cifras a palabras de forma determinista **después del guardián** (que valida los dígitos contra `calc_trace`) y justo antes del TTS: Explicador → guardián → `voice/` → TTS. El texto en pantalla conserva los dígitos. Función pura con tests propios: importes (miles y decimales), porcentajes, puntos y fechas. Detalle en la entrada `D-041` de `docs/decisiones.md` (IDs de ElevenLabs).
**Calentamiento:** la primera llamada con una voz tarda 7–11 s hasta el primer byte; las siguientes, ~150 ms. Haz una llamada de calentamiento al arrancar el backend con `ELEVENLABS_VOICE_ID`.
**IDs:** ya están en `.env.example` (`scribe_v2_realtime`, `eleven_flash_v2_5`, voz Ciro). `language_code=es` funciona en Scribe.

### T1-18 · T1-19 · T1-20 · Base del frontend que deja T0-07 — Marcos
**Qué hay en `main`:** scaffold en `frontend/` (Vite, TS estricto, Tailwind 4, TanStack Query, `react-router`). Rutas `/inicio`, `/cartera`, `/pregunta` (dentro de `AppShell`, con pestañas abajo) y `/panel` (layout de escritorio). Decisión D-035; contexto en `PRODUCT.md` y `DESIGN.md`.
**Dónde está cada cosa:**
- **Tokens:** `frontend/src/index.css`, bloque `@theme`. Son clases de Tailwind: `bg-paper`, `bg-surface`, `text-ink`, `text-ink-muted`, `border-line`, `text-accent`, `rounded-card`, `min-h-touch` (44 px) y los tres estados `text-tranquilo` / `bg-tranquilo-bg`, `text-atento` / `bg-atento-bg`, `text-revisa-plan` / `bg-revisa-plan-bg`. Texto base de 18 px. Valores y reglas en `DESIGN.md` (sin rojos, estado siempre con color + palabra, sin sombras, objetivos de 44 px). No añadas colores sueltos: si falta un token, se añade en `@theme` y en `DESIGN.md`.
- **Formato de cifras:** `frontend/src/lib/format.ts`: `formatEur`, `formatEurRange`, `formatPercent`, `formatUnits`, `formatDate`. Los importes llegan como string Decimal y se pasan tal cual; no los conviertas a `number`.
- **API y mocks:** `frontend/src/api/client.ts`. `apiGet<T>(path, { mock: "NombreDelEsquema" })` llama a `/api/v1/...` (el proxy de Vite reenvía `/api` sin reescribirlo; destino en `KAIROS_API_PROXY`, ver `frontend/.env.example`). Con `VITE_USE_MOCKS=true` lee `src/api/mocks/<Modelo>.json`, que rellena `make gen-api` (T0-03). Hasta entonces falla con `ApiError` de código `mock_missing`: pinta un estado vacío honesto, sin cifras inventadas. Los hooks de TanStack Query van en `src/api/hooks/` (carpeta aún sin crear; es de T2-13 para el polling).
- **Dónde poner tu trabajo:** T1-18 en `src/widget/`; T1-19 en `src/app/onboarding/` y `src/app/portfolio-picker/`; T1-20 en `src/app/operations/` y `src/app/dca/`. Las páginas `InicioPage`, `CarteraPage` y `PreguntaPage` de `src/app/` son marcadores de posición: se enganchan desde ahí.
- **Scripts (en `frontend/`):** `npm run dev | build | lint | typecheck | test`. Hay tests de ejemplo en `src/App.test.tsx` y `src/lib/format.test.ts`.
**Pendientes que afectan a estas tareas:**
- Alons (T0-01) debe confirmar que el backend monta los routers en `/api/v1` (*Peticiones de contrato*).
- Hasta T0-03 no hay tipos generados ni mocks en `src/api/{generated,mocks}/`.
- `playwright-cli` en Windows necesita `--browser=msedge` (ver *Bloqueos*).
**Ficheros tocados:** todo `frontend/` salvo `Dockerfile`, `PRODUCT.md`, `DESIGN.md`, `.impeccable/design.json`, `docs/decisiones.md` (D-035) y `docs/SPEC.md` §2 (React 19, Tailwind 4).

### T1-01 · Modelos + migración — Alons
**Estado:** PR #17 (`t1-01/db-models`) abierto, con CI y tests en verde en local; falta un revisor y el merge.
**Qué hay:** `models.py` en 7 módulos, registro en `backend/app/models.py`, `backend/alembic.ini` y migración `0001`. Se han añadido las tablas `dca_execution`, `dca_execution_line` y `demo_adjustment` (decisión `D-XXX` en el PR).
**Siguiente paso exacto:** revisar y hacer merge del PR #17; luego `docs: done T1-01`. Se desbloquean T1-02, T1-03 y T2-01.
**Ficheros tocados:** los de la fila, más `backend/alembic.ini`, `backend/app/models.py`, `backend/app/prices/__init__.py`, `backend/tests/{test_migrations,conftest}.py`, `backend/pyproject.toml` (isort), `docs/{SPEC,decisiones}.md`.

## 5. Bloqueos

| Fecha/hora | Tarea bloqueada | Por qué | Necesita de | Estado |
| --- | --- | --- | --- | --- |
| 2026-11-08 | Ninguna (tarea menor de setup) | `playwright-cli` no encuentra Chrome en Windows (`chrome.exe` no instalado) y hay que usar `--browser=msedge`. Hay que hacer que `scripts/setup-dev.sh` deje a `playwright-cli` usando su propio Chromium | Quien coja la tarea menor de `scripts/setup-dev.sh` | Abierto |
| 2026-11-08 | T0-05 | `EventImpactOut` (T0-04) no está en `main`; `agents` usa `EventImpactStub` | T0-04 (Jaime) | Abierto: sustituir `EventImpactStub` por `schemas.impact.EventImpactOut` al subir T0-04 |

## 6. Peticiones de contrato

Cambios en `backend/app/schemas/` o en endpoints. Los contratos se cierran en la fase 0; después solo se cambian con un PR propio (sin mezclar implementación) y avisando al equipo.

| Fecha/hora | Pide | Esquema / endpoint | Cambio | Afecta a | Estado |
| --- | --- | --- | --- | --- | --- |
| 2026-11-08 | Marcos (T0-07) a Alons (T0-01) | Prefijo de la API | Confirmar que `main.py` monta todos los routers bajo `/api/v1` (`SPEC.md` §11). El cliente del frontend usa la base `/api/v1` y el proxy de Vite reenvía `/api` tal cual | T0-01, T0-03, T0-07 y todo el frontend | Confirmado: `main.py` monta todos los routers de `app/api/` bajo `/api/v1` (D-034); todas las rutas del OpenAPI empiezan por `/api/v1/` (lo comprueba `test_gen_api.py`) |
| 2026-11-08 | Marcos (T0-05) a Jaime (T0-04) | `ExplanationStatus`, `SentenceStatus`, `StatusState`, `StatusFacts` | Importar de `app.schemas.agents` en `schemas/impact.py` y `schemas/status.py` (no redefinirlos). `StatusFacts` es la entrada de `agents.write_status_sentence`; el módulo `status` la rellena | T0-04, T1-17, T2-04 | Pendiente de confirmar |

## 7. Preguntas abiertas

| # | Pregunta | Quién decide | Estado |
| --- | --- | --- | --- |
| Q1 | Asignación de roles entre Manu, Jaime, Marcos, Alons y Javi | Equipo | Cerrada: ya no hay roles; pool de tareas por fases (D-016) |
| Q2 | Fechas del hackathon | Equipo | Cerrada: Dom 8 tarde → Mié 11 23:59 |
| Q3 | Laura tiene RV 76 % con objetivo 70 %: el paso 1 la quiere en "Tranquilo" | Equipo | Cerrada: `drift_threshold` por defecto 0,10 (D-022) |
| Q4 | "¿Voy bien?" (paso 7) depende de F11 | Equipo | Cerrada: F11 mínima (plan + proyección) pasa a MVP (D-023) |
| Q5 | Qué 3-4 eventos reales usar en el replay | Equipo | Cerrada: BCE 5 jun 2025, petróleo 13 jun 2025 y resultados de NVIDIA 26 feb 2025, a verificar en T0-10 y T1-09 (D-020) |
| Q6 | Fuente de consenso para medir la sorpresa | Equipo | Cerrada: solo en el BCE; el resto `consensus: null` (D-021) |
| Q7 | Modelo de negocio del pitch: B2B2C principal | Equipo | Abierta |
| Q8 | Disponibilidad de cada uno de lunes a miércoles (trabajo, clases) | Equipo | Abierta |

## 8. Registro de checkpoints

| Fecha/hora | Resumen (3 líneas) | Decisiones validadas |
| --- | --- | --- |
| | | |

## 9. Equivalencias de IDs antiguos y nuevos

Los IDs `T-P<n>-<nn>` ya no se usan. Esta tabla sirve para leer commits, notas y ramas antiguas.

| Antiguo | Nuevo | Antiguo | Nuevo |
| --- | --- | --- | --- |
| T-P1-01 | T0-01 | T-P3-03 | T1-15 |
| T-P1-02 | T1-01 | T-P3-04 | T1-16 |
| T-P1-03 | T0-02 | T-P3-05 | T1-17 |
| T-P1-04 | T1-03 | T-P3-06 | T2-08 |
| T-P1-05 | T1-02 | T-P3-07 | T3-01 |
| T-P1-06 | T1-04 | T-P3-08 | T2-09 |
| T-P1-07 | T1-05 | T-P4-01 | T0-07 |
| T-P1-08 | T1-06 | T-P4-02 | T1-18 |
| T-P1-09 | T2-01 | T-P4-03 | T1-19 |
| T-P1-10 | T1-07 | T-P4-04 | T1-20 |
| T-P1-11 | T2-03 | T-P4-05 | T2-10 |
| T-P1-12 | T0-03 | T-P4-06 | T2-11 |
| T-P1-13 | T3-05 | T-P4-07 | T2-12 |
| T-P1-14 | T2-02 | T-P4-08 | T3-02 |
| T-P2-01 | T0-04 | T-P4-09 | T2-13 |
| T-P2-02 | T1-10 | T-P5-01 | T0-08 |
| T-P2-03 | T1-11 | T-P5-02 | T1-08 |
| T-P2-04 | T1-12 | T-P5-03 | T1-09 |
| T-P2-05 | T1-13 | T-P5-04 | T0-09 |
| T-P2-06 | T2-04 | T-P5-05 | T1-21 |
| T-P2-07 | T2-05 | T-P5-06 | T2-14 |
| T-P2-08 | T1-14 | T-P5-07 | T3-06 |
| T-P2-09 | T3-03 | T-P5-08 | T3-07 |
| T-P2-10 | T2-06 | T-P5-09 | T3-08 |
| T-P2-11 | T2-07 | T-P5-10 | T0-06 |
| T-P2-12 | T3-04 | T-P5-11 | T2-15 |
| T-P3-01 | T0-05 | T-P5-12 | T2-16 |
| T-P3-02 | T0-10 |  |  |

`T-P3-02` ("3 + 5") era una sola tarea compartida y sigue siéndolo (T0-10). "3 ensayos" no tenía ID y ahora es T3-09.
