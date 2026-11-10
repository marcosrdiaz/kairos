# Tablero del equipo — KAIROS

Documento vivo: qué tareas hay, quién ha cogido cada una, en qué estado está y qué bloquea a quién. Lo leen y escriben las personas y sus sesiones de Claude Code.

**Plazo:** domingo 8 de noviembre (tarde) → **miércoles 11 de noviembre a las 23:59** (cierre del formulario de BEST UC3M). Entrega interna antes de las 21:00.

## Reglas

- **No hay roles ni carpetas con dueño.** Somos 5 (Manu, Jaime, Marcos, Alons y Javi) y cualquiera puede coger cualquier tarea.
- **Coger una tarea** = commit de claim en este fichero **antes de empezar**: pon tu nombre en *Cogida por* y el estado en `🔄 en curso`. Si ya está cogida, elige otra. Usa `/coger <ID>`.
- **Propiedad por tarea.** Mientras una tarea está en curso, quien la tiene es dueño de los ficheros de su columna *Ficheros que toca*. Otra sesión no los edita: si necesita algo de ellos, apunta un bloqueo (§ Bloqueos). Por eso no se coge una tarea cuyos ficheros solapen con los de otra en curso.
- **Dependencias.** Si una tarea depende de otra, se hace antes la dependencia. `(b)` = dependencia blanda: se puede empezar con mocks o datos de prueba.
- **Fases.** Una fase está **cerrada** cuando todas sus tareas están en `main` con `make lint && make test` en verde. Se puede **adelantar** una tarea de la fase siguiente solo si todas sus dependencias están hechas.
- **Excepciones a la propiedad por tarea:** `docs/decisiones/` (cada decisión es un fichero nuevo `D-XXX-<slug>.md`; `docs/decisiones.md` es solo el índice generado y no se edita) y tu propia fila de este tablero.
- **El tablero solo se modifica con commits directos a `main`** (excepción a "todo por PR"), nunca dentro de un PR, y el commit toca únicamente `docs/TABLERO.md`. Mensaje `docs: claim|release|done|block|note T<x>-<nn>`: `claim`, `release` y `done` cambian la fila de la tarea; `block` apunta o cierra una fila de *Bloqueos* (y marca `⛔`); `note` actualiza *Notas para retomar* o *Peticiones de contrato* (y marca `🧪 en PR`). Flujo: `git pull --rebase` → comprobar (p. ej. que la tarea sigue libre) → commit → `git push` justo después. Si el push falla, se repite desde el pull. Excepción puntual: `docs: tablero rules` para cambios de reglas de este propio tablero. Todo lo demás va por PR: el merge lo hace quien abre el PR, tras la aprobación de un revisor y con el CI en verde.
- **Estados:** `⬜ pendiente` · `🔄 en curso` · `🧪 en PR` · `✅ hecho` · `⛔ bloqueado`. Marcar `✅ hecho` (`docs: done T<x>-<nn>`) solo con la tarea en `main`.
- **Decisiones sin mergear: por título, nunca `D-XXX`.** En el tablero (que no va en PRs) una decisión de un PR aún sin mergear se cita por su título. La Action `renumber-decisions` solo renumera los ficheros del PR que entra en `main`, así que un `D-XXX` aquí no se numera, o apuntaría a la decisión de otro PR.
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
| **Dom 8 · 23:59** | **Fase 0 cerrada**: esqueleto del repo en `main`, contratos y mocks publicados, datos de ejemplo empezados | ✅ |
| **Lun 9** | **Fase 1 cerrada**: datos y motores contra el backend real. Look-through y eventos, antes de las 14:00 | ✅ |
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
| T0-04 | Esquemas §4.3 (impacto, exposición, radar, estado, proyección, agenda, move, escenario) + ejemplos + mocks | Ejemplos validan; los endpoints responden con mock | T0-01 | `backend/app/schemas/{impact,exposure,radar,status,planning}.py`, `backend/app/schemas/examples/` (esos modelos), `backend/app/{exposure,impact,status,planning}/{mock,service}.py`, `backend/app/api/{exposure,impact,status,planning}.py` | Jaime | ✅ hecho |
| T0-05 | Esquemas §4.2 y §4.4 (`EventAnalysis`, `ShockSet`, Ask SSE, Guardián, `ExplainerContext`, `AlertOut`) + ejemplos + mocks; el `/ask` mock emite SSE de ejemplo | El frontend recibe el SSE mock | T0-01 | `backend/app/schemas/{events,agents,alerts}.py`, `backend/app/schemas/examples/` (esos modelos), `backend/app/{agents,events,alerts}/{mock,service}.py`, `backend/app/api/{ask,events,alerts}.py`, `backend/app/{agents,events,alerts}/__init__.py`, `backend/tests/test_event_agent_examples.py` | Marcos | ✅ hecho |
| T0-06 | Contrato de voz §4.5 + mock (`/voice/tts` devuelve un mp3 fijo) | El frontend reproduce el mp3 mock | T0-01 | `backend/app/schemas/voice.py`, `backend/app/schemas/examples/` (voz), `backend/app/voice/{mock,service}.py`, `backend/app/api/voice.py`, `data/voice/mock.mp3` | Alons | ✅ hecho |
| T0-07 | Vite + TS + Tailwind + TanStack Query; 3 pestañas (Inicio · Cartera · Pregunta) y ruta `/panel` vacía. El enganche a los mocks espera a T0-03 | Navega sobre mocks | T0-03 (b) | `frontend/` salvo `Dockerfile`, `src/voice/`, `src/api/{generated,mocks}/`; `PRODUCT.md`, `DESIGN.md` | Marcos | ✅ hecho |
| T0-08 | `assets.json`, `laura.json` / `javier.json` con plan y DCA según §5, y `assumptions.json` (rentabilidad por clase de activo, con fuente y `"illustrative": true`) | Cumple la fila 1 de §5; `assumptions.json` listo para la proyección | — | `data/seed/assets.json`, `data/seed/portfolios/`, `data/seed/assumptions.json` | Jaime | ✅ hecho |
| T0-09 | Verificar IDs de Scribe v2 Realtime y Flash v2.5, y la voz en español; medir latencia | Anotado en `decisiones.md` | — | `docs/decisiones.md` (solo añadir) | Marcos | ✅ hecho |
| T0-10 | Confirmar los 3 eventos (decisión 5 de §8) y redactar `title`, `text`, `source_urls`, `consensus`, `fallback_chain` | JSON sin `observed` todavía. Límite: lunes 14:00 | — | `data/events/replay/*.json` | Manu | ✅ hecho |

### Fase 1 · Datos y motores (lun 9)

| ID | Tarea | Criterio de hecho | Depende de | Ficheros que toca | Cogida por | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| T1-01 | Modelos + migración (`SPEC.md` §6) | `alembic upgrade head` | T0-01 | `backend/alembic/`, `backend/app/{portfolio,prices,exposure,impact,events,alerts,agents}/models.py` | Alons | ✅ hecho |
| T1-02 | `prices`: proveedor offline (CSV) + FX + `latest()` + `history()` | RF-03. Con CSV de prueba hasta que T1-09 esté | T1-01, T1-09 (b) | `backend/app/prices/`, `backend/tests/fakes/price_provider.py` | Alons | ✅ hecho |
| T1-03 | Alta de posiciones + seed + `/demo/reset` + `/assets/lookup` | RF-01, RF-02 | T1-01, T0-08 | `backend/app/portfolio/{service,repository,engine}.py`, `backend/app/api/{portfolio,demo,assets}.py`, `scripts/seed_db.py`, `backend/tests/golden/portfolio_init*` | Alons | ✅ hecho |
| T1-04 | Compra/venta FIFO con casos dorados | RF-04, RF-05 | T1-03 | `backend/app/portfolio/{service,repository,engine,lots}.py`, `backend/tests/golden/portfolio_fifo*` | Alons | ✅ hecho |
| T1-05 | Traspaso fondo → fondo + error con alternativa | RF-06 | T1-04 | `backend/app/portfolio/{service,transfers}.py`, `backend/tests/test_transfers.py` | Alons | ✅ hecho |
| T1-06 | DCA (planes, ejecución pendiente, confirmar/saltar, `/demo/dca/run`) | RF-07. Límite: martes 10:00 | T1-04 | `backend/app/portfolio/{service,dca}.py`, `backend/app/api/dca.py`, `backend/tests/test_dca.py` | Alons | ✅ hecho |
| T1-07 | `/plan` + `get_value_change` | RF-22 (datos) | T1-03 | `backend/app/portfolio/{service,plan}.py`, `backend/app/api/plan.py`, `backend/tests/test_plan.py` | Alons | ✅ hecho |
| T1-08 | Composición de los fondos/ETF de Laura y Javier (top-N + "Otros", `as_of`, fuente) | CSV completos; ≥ 90 % de cobertura en Laura. Límite: lunes 14:00 | — | `data/seed/compositions/`, `backend/tests/test_compositions.py` | Marcos | ✅ hecho |
| T1-09 | Históricos diarios de 2–3 años (activos y factores) + `observed` de los 3 eventos calculado de esos datos | `data/prices`, `data/factors`, replay completo | T0-10 | `data/prices/`, `data/factors/`, `data/events/replay/*.json` (solo `observed`), `scripts/fetch_prices.py` | Jaime | ✅ hecho |
| T1-10 | Casos dorados Laura/Javier (exposición, 3 eventos, proyección) en hoja | Revisado por otra persona | T0-08, T1-08 | `backend/tests/golden/{exposure,impact,projection}*` | Alons | ✅ hecho |
| T1-11 | Look-through, solapamientos y `radiography` | RF-08, RF-09. Límite: lunes 14:00 | T1-08 | `backend/app/exposure/{service,engine,repository}.py`, `backend/app/api/exposure.py`, `backend/tests/test_exposure*.py` | Jaime | ✅ hecho |
| T1-12 | `compute_betas.py` + `factor_beta` | Betas con R², error estándar y n | T1-09, T1-01 | `scripts/compute_betas.py`, `backend/app/impact/{betas,repository}.py` | Manu | ✅ hecho |
| T1-13 | Motor de impacto: mercado, divisa, resultados, rango, confianza, polaridad; `estimate_scenario` comparte núcleo | RF-10 + dorados | T1-12 | `backend/app/impact/{service,engine,scenario}.py`, `backend/app/api/impact.py`, `backend/tests/test_impact*.py` | Jaime | ✅ hecho |
| T1-14 | Proyección con DCA (`ProjectionOut`) en `planning/` | Dorado de Laura `on_track: true` | T1-07, T0-08 | `backend/app/planning/{service,projection}.py`, `backend/app/api/planning.py`, `backend/tests/test_projection.py` | Alons | ✅ hecho |
| T1-15 | Analizador + `build_shockset` + pipeline de §2 + `/demo/replay` (impacto con mock al principio) | RF-11, RF-12; fallback probado | T0-10 | `backend/app/agents/{analyzer,service}.py`, `backend/app/agents/prompts/analyzer.md`, `backend/app/events/`, `backend/app/api/events.py`, `scripts/replay_event.py` | Jaime | ✅ hecho |
| T1-16 | Guardián: patrones, cifras, forma; un test por patrón y por formato de número | RF-16 | T0-05 | `backend/app/agents/guardian.py`, `backend/app/agents/prompts/forbidden.yaml`, `backend/tests/test_guardian*.py`, `backend/tests/fakes/` | Manu | ✅ hecho |
| T1-17 | Explicador: contexto precargado + herramientas + `/ask` SSE + reintento + plantilla | 3 preguntas tipo responden con FakeClaude y con Claude real | T1-16 | `backend/app/agents/{explainer,tools,context,service}.py`, `backend/app/agents/prompts/explainer.md`, `backend/app/api/ask.py` | Manu | ✅ hecho |
| T1-18 | Pantalla de inicio simulada con widget (3 estados, color + palabra) | RF-13 visual | T0-07 | `frontend/src/widget/` | Javi | ✅ hecho |
| T1-19 | Alta de cartera + selector Laura/Javier (`?p=`) | RF-01, RF-02 | T0-07 | `frontend/src/app/onboarding/`, `frontend/src/app/portfolio-picker/` | Alons | ✅ hecho |
| T1-20 | Operaciones (compra, venta, traspaso con error explicado) y DCA | RF-04–07 en UI | T0-07 | `frontend/src/app/operations/`, `frontend/src/app/dca/` | Manu | ✅ hecho |
| T1-21 | `voice/` backend: STT por WS, TTS de frases aprobadas, disclaimer | Audio de ida y vuelta con frase fija | T0-06, T0-09 | `backend/app/voice/`, `backend/app/api/voice.py`, `data/voice/disclaimer.mp3` | Javi | ✅ hecho |
| T1-22 | Tema claro/oscuro: tokens `--kairos-color-*` de los dos modos, interruptor accesible y estilo visual nuevo (paleta dorada, barra lateral en escritorio) | Interruptor usable con teclado y lector de pantalla; preferencia guardada y sin parpadeo al cargar; un test comprueba contraste ≥ 4,5:1 (texto) y ≥ 3:1 (bordes y foco) en los dos modos | T0-07 | `frontend/index.html`, `frontend/src/index.css`, `frontend/src/styles/`, `frontend/src/theme/`, `frontend/src/components/`, `frontend/src/app/AppShell.tsx`, `DESIGN.md` | Javi | ✅ hecho |
| T1-23 | Tests del backend más rápidos: `pytest-xdist` (`-n auto` en `make test-backend`) y fixture `db` sin `drop_all` innecesario | `make test` en verde y en menos de la mitad de tiempo que antes (~2 min en local) | T0-01 | `backend/pyproject.toml`, `backend/uv.lock`, `backend/tests/conftest.py`, `Makefile` (solo `test-backend`) | Alons | ✅ hecho |

### Fase 2 · Experiencia e integración (hasta el mar 10, 18:00)

| ID | Tarea | Criterio de hecho | Depende de | Ficheros que toca | Cogida por | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| T2-01 | `/traces/{calc_id}` con `parent_calc_ids` | RF-19 | T1-01 | `backend/app/core/trace.py`, `backend/app/api/traces.py` | Marcos | ✅ hecho |
| T2-02 | Ajuste de demo: `portfolio.service.apply_demo_adjustment(...)` (lo llama `events` tras el impacto) + `demo_adjustments` en la valoración + borrado en `/demo/reset` | Tras el replay, `/portfolios/laura` y `/status` reflejan el impacto con etiqueta y traza | T1-03, T1-13 | `backend/app/portfolio/{service,repository,engine}.py`, `backend/app/api/demo.py` | Alons | ✅ hecho |
| T2-03 | Integración: quitar mocks del backend módulo a módulo; `/demo/clock`; smoke del guion por API | Smoke en verde (`scripts/demo_smoke.py`) | Todas las de la fase 1 | `backend/app/*/mock.py` (borrar), `backend/app/api/demo.py`, `scripts/demo_smoke.py` | Jaime | 🧪 en PR |
| T2-04 | `status` precalculado + `recompute` + frase vía `agents.write_status_sentence` | RF-13; `/status` < 200 ms | T1-13, T1-17 | `backend/app/status/`, `backend/app/api/status.py` | Jaime | ✅ hecho |
| T2-05 | Radar (6 reglas, plantillas, invariante de oportunidad) | RF-18 | T1-11, T1-06 | `backend/app/exposure/{radar,templates}.py`, `backend/app/api/radar.py`, `backend/tests/test_radar*.py`, `backend/app/api/exposure.py`, `backend/app/exposure/{service,mock}.py` (solo la parte del radar) | Marcos | ✅ hecho |
| T2-06 | Agenda (`agenda.json` + DCA + exposición por factor) | Bloque del panel con datos | T1-12, T2-15 | `backend/app/planning/{agenda,service,mock}.py`, `backend/app/impact/service.py` (solo `get_factor_betas`), `backend/tests/{test_agenda,test_analysis_mocks}.py`, `scripts/demo_smoke.py` (paso 5) | Alons | ✅ hecho |
| T2-07 | `explain_move` | "¿Por qué ha bajado?" con dato real | T1-07, T1-13 | `backend/app/impact/move.py`, `backend/app/api/move.py`, `backend/tests/test_move.py` | Alons | ✅ hecho |
| T2-08 | Avisos: score, umbral, límite semanal, mensaje validado | RF-23 (`kind=event_impact` es MVP porque lo usa el paso 3) | T1-13 | `backend/app/alerts/`, `backend/app/api/alerts.py` | Marcos | ✅ hecho |
| T2-09 | Explicaciones de evento por cartera + invalidación del contexto precargado | `explanation_status: ok` en los 3 eventos × 2 carteras | T1-15, T1-13 | `backend/app/events/pipeline.py`, `backend/app/agents/context.py` | Jaime | 🧪 en PR |
| T2-10 | Panel: resumen, eventos (cadena, €, rango, confianza, filtro), exposición, radar, agenda | RF-17 | T0-04, T0-07 | `frontend/src/panel/`, `frontend/src/api/hooks/{useEvents,useLivePortfolio,useExposure,useRadar,useAgenda}.ts` (nuevos) | Marcos | ✅ hecho |
| T2-11 | "¿De dónde sale?" → traza desde cualquier cifra | RF-19 | T2-01 | `frontend/src/components/trace/` | Jaime | ✅ hecho |
| T2-12 | Avisos de IA y "no es asesoramiento"; accesibilidad | RF-20, RNF-11 | T0-07 | `frontend/src/components/notices/`, `frontend/src/index.css` | Javi | ✅ hecho |
| T2-13 | Polling de `/status` y `/alerts` cada 5 s; aviso en pantalla de inicio (paso 3) | El widget cambia solo tras un replay | T2-04, T2-08 | `frontend/src/api/hooks/`, `frontend/src/widget/` | Jaime | ✅ hecho |
| T2-14 | `src/voice/`: push-to-talk, cola de audio por frase, disclaimer, plan B de preguntas sugeridas | RF-14 de punta a punta | T1-21, T1-17 | `frontend/src/voice/` | Javi | ✅ hecho |
| T2-15 | `agenda.json`, `DEMO_CLOCK` y revisión de los datos contra §5 | Las 5 filas de §5 se cumplen | T1-11, T1-13 | `data/events/agenda.json`, `data/seed/portfolios/` | Jaime | ✅ hecho |
| T2-16 | Medir latencia de voz (10 intentos) | 8/10 por debajo de 2 s o, si no, cambiar de modelo (decisión 4) | T2-14 | `scripts/measure_voice.py`, `docs/decisiones/` (fichero nuevo) | Javi | ✅ hecho |
| T2-17 | Ticker de mercado en Inicio (entre la cabecera de estado y las tarjetas): barra que se desplaza sola con el último precio y la variación de los activos de la cartera | Precios reales con fecha (sin cifras inventadas); se pausa al pasar el ratón, con el foco y con un botón (WCAG 2.2.2); sin movimiento con `prefers-reduced-motion`. Necesita un endpoint de precios nuevo: petición de contrato en un PR propio | T1-02 | `backend/app/api/prices.py` (nuevo), `backend/app/prices/{ticker,service}.py`, `backend/tests/test_ticker*.py`, `frontend/src/app/market/ticker/`, `frontend/src/api/hooks/useTicker.ts` (nuevo), `frontend/src/app/InicioPage.tsx` (solo montar el ticker) | Jaime | 🧪 en PR |
| T2-18 | Gráfica interactiva de la evolución del valor de la cartera en Inicio (contenedor grande junto al ticker) | Serie real calculada con `prices.history` (sin datos inventados); selector de periodo; punto activo con ratón y teclado; tabla alternativa para lector de pantalla. Necesita `GET /portfolios/{id}/history` y su esquema: petición de contrato en un PR propio. Si usa una librería de gráficos, decisión antes | T1-02, T1-03 | `backend/app/portfolio/history.py`, `backend/app/api/history.py` (nuevo), `frontend/src/app/market/chart/` | Javi | 🔄 en curso |
| T2-19 | Resumen de noticias en Inicio (debajo de las tarjetas): carrusel con ilustración por tipo de evento a la izquierda y texto a la derecha, flechas y avance automático cada 10 s | Datos de `GET /portfolios/{id}/events` (rango en €, confianza, fuente); botón de pausa y pausa con ratón y foco (WCAG 2.2.2); flechas usables con teclado; sin avance automático con `prefers-reduced-motion` | T1-13 | `frontend/src/app/news/` | Javi | ✅ hecho |
| T2-20 | *Propuesta (Q9, pendiente del checkpoint).* Bandeja de avisos en la app: campana en la cabecera con contador de no leídos y lista de avisos (mensaje, fecha, impacto en € con rango y "¿De dónde sale?") que se pueden marcar como leídos | Datos de `GET /portfolios/{id}/alerts` (sin avisos inventados); contador actualizado por el polling de T2-13; campana y lista usables con teclado y lector de pantalla; aviso "no es asesoramiento" visible. Marcar como leído necesita una ruta nueva (p. ej. `POST /alerts/{id}/read`): petición de contrato en un PR propio | T2-08, T2-13 | `frontend/src/app/alerts/` | — | ⬜ |
| T2-21 | *Propuesta (Q9, pendiente del checkpoint).* Aviso por movimiento de mercado (`kind=market_move`): si la cartera varía en un día por encima del umbral de aviso y no hay evento que lo explique, se genera un aviso con la explicación de `explain_move` | Comparte la puntuación, el umbral y el límite de 2 por semana ISO con `event_impact` (D-032); mensaje validado por el guardián, sin órdenes ("calmar antes que alarmar"); cifras con `calc_id`; test del límite compartido. Añadir `market_move` a `AlertKind` es una petición de contrato en un PR propio | T2-07, T2-08 | `backend/app/alerts/market_move.py`, `backend/tests/test_alerts_market_move.py` | — | ⬜ |
| T2-22 | *Propuesta (Q9, pendiente del checkpoint).* Marcadores de noticias en la gráfica de la cartera (T2-18): un punto en la fecha de cada evento que afecta a la cartera; al pasar el ratón o con el foco, una tarjeta con el título, una descripción breve, el movimiento observado del mercado (factores del `ShockSet`) y el impacto en la cartera con rango, confianza y "¿De dónde sale?" | Datos de `GET /portfolios/{id}/events` (ninguna cifra del LLM); marcadores usables con teclado y anunciados al lector de pantalla; incluidos en la tabla alternativa de T2-18. Fecha del marcador: la real del evento, no la del replay | T2-18 | `frontend/src/app/market/chart/markers/` | — | ⬜ |
| T2-23 | *Propuesta (Q9, pendiente del checkpoint).* Gráfica de valor/tiempo por activo (acción, fondo o ETF) desde la posición, con los marcadores de T2-22 filtrados a los eventos que afectan a ese activo y su impacto en esa posición | Serie real de `prices.history` (VL diario en fondos); impacto por posición del motor de impacto con `calc_id`. Necesita un endpoint de histórico por activo (p. ej. `GET /portfolios/{id}/positions/{asset_id}/history`): petición de contrato en un PR propio | T2-18, T2-22 | `backend/app/api/asset_history.py` (nuevo), `frontend/src/app/market/asset-chart/` | — | ⬜ |
| T2-24 | *Propuesta (Alons, pendiente de validar en la llamada diaria).* Modo producción con precios en directo (RF-03 y D-026, que no tenían tarea): adaptador de Yahoo detrás de la interfaz `PriceProvider` (acciones y ETF intradía, VL diario de fondos, EUR/USD), con caché en las tablas `price` y `fx_rate`. Detalle en D-065 | El modo demo (`MARKET_DATA_PROVIDER=offline`) no cambia y el guion sigue en verde. Con `DEMO_MODE=false` y `MARKET_DATA_PROVIDER=yahoo`, `/portfolios/laura` valora con precios del día y `price_at` real. Si el proveedor falla, se sirve el último precio guardado con su fecha y nunca uno inventado. Tests con un proveedor falso (sin red en CI) y uno `@pytest.mark.live`. `/health` muestra el modo. Sin dependencias nuevas | T1-02 | `backend/app/prices/`, `backend/app/config.py`, `.env.example`, `backend/tests/test_prices_live.py` | — | ⬜ |
| T2-25 | Betas en el arranque: el servicio `seed` ejecuta `compute_betas.py` después de `seed_db.py` (así lo hacen `make up` y `make seed`) | Tras `docker compose down -v && docker compose up --build`, `factor_beta` tiene filas y los eventos del replay salen con rango abierto (`low_eur < high_eur`). Ver *Bloqueos* (rangos del impacto) | T1-12 | `docker-compose.yml`, `scripts/compute_betas.py` (solo si hace falta), `Makefile` (solo `seed` y `betas`, si hace falta) | Marcos | ✅ hecho |
| T2-27 | Cadena causal del BCE: reescribir `fallback_chain` (y `text` si hace falta) de `bce-2025-06.json` para que cuadre con `observed`: el BCE baja tipos pero ya estaba descontado, la rentabilidad del bono sube ligeramente (`RATES_EUR` +), la renta fija cede algo y el euro se fortalece (`EURUSD` +), así que los activos en dólares valen algo menos en euros. Sin cifras | La cadena mostrada cuadra con el signo de los impactos de Laura y Javier tras `demo/reset` con `preload` y replay; el guardián y los tests de eventos siguen en verde. Ver *Bloqueos* (narrativa del BCE) | T0-10 | `data/events/replay/bce-2025-06.json` | Marcos | ✅ hecho |
| T2-26 | Analizador sin influencia en las cifras y coherente con el dato: las cifras se calculan siempre con **todos** los factores de `observed`; `channels` solo sirve para la narrativa; la dirección observada va al prompt y se valida; timeout de 10 s; caché del análisis y pre-análisis de los 3 eventos | Con `ANTHROPIC_API_KEY`, los 3 eventos salen analizados por el modelo (no `fallback`), con `channels[].direction` igual al signo de `observed` y las mismas cifras que sin analizador; repetir el replay no llama al modelo. Detalle en *Notas para retomar* (T2-26) | T1-15, T2-09 | `backend/app/agents/{analyzer,service}.py`, `backend/app/agents/prompts/analyzer.md`, `backend/app/events/{pipeline,service,repository}.py`, `scripts/preanalyze_events.py` (nuevo), `backend/tests/test_analyzer*.py`, `backend/tests/test_events_pipeline.py` | — | ⬜ |

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

### T2-17 · Ticker de mercado en Inicio — Jaime
**Qué estaba haciendo:** el contrato (#84) está en `main`. La implementación (#85) se mergeó en la rama de #84 y no en `main`, así que **`GET /portfolios/{id}/ticker` en `main` aún responde `UPSTREAM_UNAVAILABLE`** y no hay ticker en Inicio. El mismo código va en #86 (`t2-17/market-ticker` → `main`).
**Siguiente paso exacto:** esperar el CI de #86, aprobación y merge. Después, `docs: done T2-17` y borrar esta nota.
**Ficheros tocados:** `backend/app/schemas/prices.py`, `backend/app/schemas/examples/TickerOut.json`, `backend/app/api/prices.py`, `backend/app/prices/{ticker,service}.py`, `backend/tests/test_ticker*.py`, `frontend/src/api/generated/`, `frontend/src/api/mocks/TickerOut.json`, `frontend/src/api/hooks/useTicker.ts`, `frontend/src/app/market/ticker/`, `frontend/src/app/InicioPage.tsx`, `docs/SPEC.md`.

### T3-04 · Umbrales de beta de la agenda — Alons (para quien coja la tarea)
**Qué hay que saber:** `planning/agenda.py` (`BETA_THRESHOLDS`, `MIN_T_STAT`) decide qué posiciones cuentan como expuestas a cada evento de la agenda (D-084, en «Propuesta»: validarla en la llamada diaria). Los umbrales son 0,001 / σ diaria de cada factor en `data/factors`; si cambian esos datos, hay que recalcularlos.

### T3-04 · Umbrales de avisos y de estado: cambiarlos a la vez — Marcos (para quien coja la tarea)
**Qué hay que saber:** `alerts/config.py` (`MIN_EUR`, `MIN_SHARE`) y `status/config.py` (`ATENTO_MIN_EUR`, `ATENTO_MIN_SHARE`) tienen que valer lo mismo: el paso 3 del guion necesita el widget en «Atento» y el aviso a la vez. Dos tests lo comprueban (`backend/tests/test_alerts_engine.py`); si cambias uno y no el otro, fallan.
**Siguiente paso exacto:** al calibrar, cambia los dos ficheros en el mismo PR. Ver D-076.

### T2-09 · Explicaciones de evento e invalidación del contexto — Jaime
**Qué estaba haciendo:** #58 y #59 ya en `main`: el pipeline y `/demo/reset` invalidan el contexto del explicador, y el contexto se conserva si al pasar el TTL los datos son los mismos (pendiente de D-071).
**Siguiente paso exacto:** con `ANTHROPIC_API_KEY` en `.env`, desde `backend/`, `pytest -m live tests/test_event_explanations_live.py -s` (criterio con Claude real, aún sin ejecutar). Si pasa, `docs: done T2-09`.
**Ficheros tocados:** `backend/app/events/{pipeline,service}.py`, `backend/app/agents/context.py`, `backend/tests/test_event_explanations{,_live}.py`, `backend/tests/test_explainer_context.py`.
**Sin hacer (D-071):** Claude a veces suma cifras en «¿Por qué ha bajado?». El guardián lo bloquea y acaba en plantilla; ajustar el prompt requiere medir con la clave.

### T2-03 · Integración sin mocks y smoke del guion — Jaime
**Qué estaba haciendo:** #76 y #78 ya en `main` (smoke en verde por HTTP con SQLite, los 8 pasos). «¿De dónde sale?» probado contra el backend real (SQLite local, replay de los 3 eventos, Edge): las cadenas de `parent_calc_ids` y el formato de € y % están bien; salían ~50 claves en inglés y valores sin traducir. Arreglado en **#82** (pendiente de revisión), que también quita `frontend/.playwright-cli/` y lo ignora.
**Siguiente paso exacto:** mergear #82 tras la revisión y marcar `docs: done T2-03`. Opcional, quien tenga Docker: smoke contra Postgres con `make up` y `cd backend && uv run python ../scripts/demo_smoke.py`.
**Visto y no tocado (de otros módulos, detalle en #82):** la `formula` de la traza de estado lleva identificadores en inglés (`status/`); en la traza de estado con evento, «Renta variable actual/objetivo» van a `null`; la traza `event_impact` guarda `explanation_status: pending`. `agent_log` sigue sin rellenarse (limitación aceptada en D-082).
**Para T2-26:** #78 cambia `_check_no_orders` de `analyzer.py`; conviene empezar T2-26 con #78 ya en `main`. **Para T2-06:** al sustituir `get_agenda`, borrar `planning/mock.py`.
**Ficheros tocados:** los de la fila, más `backend/app/agents/{analyzer,guardian}.py`, `backend/app/config.py`, `.env.example`, `docs/SPEC.md`, `backend/app/schemas/demo.py`, `frontend/src/api/{generated,mocks}/`; en #82, `frontend/src/components/trace/{labels,traceFields,traceFields.test}.ts`, `.gitignore` y `frontend/.playwright-cli/` (borrada).

### T2-26 · Analizador: cifras con todos los factores, dirección validada y caché — Marcos (para quien coja la tarea)
**Por qué:** con Claude real, la dirección de `channels` contradice `observed` (BCE: tipos y euro; NVIDIA: bolsa global) y, como `pipeline.py` usa `channels` para elegir qué factores entran en el `ShockSet`, el modelo puede cambiar una cifra. Detalle y mediciones en *Bloqueos* (analizador). Cambia el criterio de «el LLM elige canales» (decisión 11 del diseño, §8, y D-025): ver la decisión «Las cifras usan todos los factores observados; el analizador solo redacta».
**Alcance:**
- **Cifras:** `build_shockset` usa siempre todos los factores de `observed` (`selected_by = all_observed`). `channels` del analizador pasa a servir solo para la narrativa. Así el LLM no influye en ningún número (regla 1 de `CLAUDE.md`).
- **Dirección:** al prompt se le pasa la dirección observada de cada factor («OIL: sube»), sin magnitudes para que no copie cifras. Tras la respuesta, `channels[].direction` se corrige al signo de `observed`. Si la `causal_chain` contradice una dirección, un reintento con feedback; si vuelve a fallar, `fallback_chain`.
- **Timeout** del analizador a 10 s (hoy 4 s: BCE y petróleo agotaban los dos intentos con latencias de 3–4 s).
- **Caché:** si `event.analysis` ya existe para ese `event_id` (y la misma versión del prompt), el replay lo reutiliza sin llamar al modelo. El `preload` deja analizados BCE y petróleo, y `scripts/preanalyze_events.py` (o un flag) pre-analiza también NVIDIA antes de la demo. La versión del prompt necesita un campo opcional nuevo en `EventAnalysis` (p. ej. `prompt_version`): petición de contrato en un PR propio (añadir un campo opcional es aceptable).
- **Tests con `FakeClaude`:** dirección contraria corregida; cadena contradictoria → reintento → `fallback_chain`; caché reutilizada (sin llamada al modelo); cifras idénticas con y sin analizador.
**Ojo con los solapes:** `T2-09` (Jaime, 🧪 en PR) declara `events/pipeline.py`: esperar a que esté en `main`. `T2-03` (Jaime) ya cambió `analyzer.py` en #78 (en `main`): ver más abajo, no hay que repetirlo. El pre-análisis va en un script nuevo, no en `api/demo.py` (lo declara T2-03).
**Empezar con #78 y T2-09 en `main`.** #78 (T2-03, ya en `main`) toca `agents/analyzer.py` solo en `_check_no_orders`: quita la regex provisional `_ORDER` y `_normalized`, e importa `guardian`; ahora rechaza el borrador si `guardian.find_forbidden(texto)` encuentra algo en `causal_chain`, `label` o `rationale` de los canales (solo patrones prohibidos: no comprueba cifras, porque el borrador no lleva ninguna). **No toca** `_TIMEOUT_S` (sigue en 4,0), `_user_message`, `_attempt` ni `analyze`. T2-26 parte de ahí: dejar `_check_no_orders` tal cual (no volver a una regex propia), y añadir la validación de dirección como función aparte, llamada desde `_attempt` junto a `_check_no_orders`, para que el reintento con feedback cubra las dos.
**Siguiente paso exacto:** coger la tarea con `/coger T2-26` cuando T2-09 esté en `main` (#78 ya lo está); empezar por el PR de contrato (`prompt_version`, ver *Peticiones de contrato*) y luego el código. Antes del PR de contrato, `git pull` y `make gen-api`: #76 también regeneró `frontend/src/api/generated/`.

### T3-06 · README: limitación conocida «sin login» — Manu (para quien coja la tarea)
- Añade al README un apartado de **limitaciones conocidas** que diga que no hay login ni usuarios: cualquiera que abra la app puede ver y modificar cualquier cartera (Laura, Javier o las que se den de alta), también registrar operaciones y planes DCA. Es una decisión del MVP (D-013, fuera del alcance en `docs/kairos-spec.md` e `INGENIERIA.md` §1): las carteras son ilustrativas, la app corre en local y no mueve dinero real.
- Trabajo futuro: cuentas de usuario con autenticación, y que cada ruta del backend compruebe que la cartera es de quien la pide.

### T3-07 · Cifras reales del paso 2 para el PDF y la presentación — Marcos (para quien coja la tarea)
**Usad estas cifras, no el ≈ 61 % ni el ≈ 19 % de la fila 2 de §5.** Look-through de Laura con las posiciones de `laura.json` y los precios de cierre del 6-nov-2026: **63,7 %** en EE. UU., **25,9 %** en las 7 mayores empresas, **76,0 %** en renta variable. Siguen marcadas como ejemplo ilustrativo. Si cambian los datos o los precios, se recalculan con el motor real (T1-11) antes de la entrega. Origen y contexto: decisión «Composición de fondos y ETF (T1-08): formato del CSV, residuos por país, divisa de los fondos cubiertos y claves de empresa».


### T2-03 · T2-06 · Lo que deja T2-15 — Jaime (para quien coja la tarea)
**T2-06:** el formato de `data/events/agenda.json` está en D-080. `company` es la clave del look-through (`NVDA`).
**T2-06 y el smoke (`scripts/demo_smoke.py`, #78):** al terminar la agenda real hay que actualizar el **paso 5** del smoke. Hoy solo comprueba `_require(agenda, "agenda vacía")` sobre `GET /portfolios/laura/agenda`, y eso pasa también con el ejemplo fijo de `planning/mock.py`: el smoke no distingue la agenda real de la mock. Debe comprobar, como mínimo, citas de `agenda.json` con fecha posterior al `DEMO_CLOCK`, la cita de DCA y los `exposed_eur`/`exposed_weight` que salen del look-through de Laura; y fallar si devuelve el ejemplo fijo. Ese fichero lo declara T2-03 (Jaime) mientras esté en curso: al coger T2-06, añadir `scripts/demo_smoke.py` a *Ficheros que toca* (o pedírselo a Jaime si T2-03 sigue abierta). Además, al sustituir `get_agenda`, borrar `planning/mock.py` (ver nota de T2-03).
**T2-03 (bloqueo de `factor_beta`):** verificado: con las betas calculadas, el rango se abre y NVIDIA da −337,06 € en Laura (−349,11 a −325,01, confianza alta) y −239,29 € en Javier.
**Todos:** quien ya tenga `.env` debe añadir `DEMO_CLOCK=2026-11-06T18:00:00Z` a mano.

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

### T2-09 · T3-09 · Lo que deja la medición de latencia de voz (T2-16) — Javi (para quien coja la tarea)
**T2-09:** el contexto precargado de Laura cambia de tamaño entre turnos sin cambiar el estado (9.213 → 9.250 tokens de caché) y obliga a recrear la caché del prompt (+1–3 s). Detalle en D-071.
**T3-09 (ensayos):** tras `/demo/reset`, haz una pregunta a Laura y otra a Javier para calentar la caché del prompt antes de empezar. Para comprobar la latencia: `cd backend && uv run python ../scripts/measure_voice.py --prepare` (8/10 por debajo de 2 s).

## 5. Bloqueos

| Fecha/hora | Tarea bloqueada | Por qué | Necesita de | Estado |
| --- | --- | --- | --- | --- |
| 2026-11-10 | Ninguna (endurecimiento de T1-23, tests en paralelo); afecta a los tests de T1-12 y T2-03 y a la fiabilidad del CI | **Fallos intermitentes con `pytest -n auto`** (`make test-backend`): `tests/test_compute_betas_script.py::test_script_writes_all_betas_and_can_be_repeated` (falló en `assert first.returncode == 0`, la salida del subproceso no se vio) y `tests/test_demo_smoke.py::test_the_whole_script_works` (error en el fixture: el subproceso terminó con código distinto de 0). En solitario pasan (`pytest tests/test_compute_betas_script.py`, `tests/test_demo_smoke.py`), y en la pasada completa siguiente pasaron las dos; con y sin los cambios de cada PR. Ocurrió 2 de 4 pasadas completas en local (Windows, todos los núcleos). **Causa probable, sin confirmar:** los dos lanzan un subproceso de Python (`subprocess.run` del script contra una SQLite temporal) que vuelve a importar la aplicación, y con `-n auto` compiten por CPU y memoria con el resto de workers hasta fallar o agotar tiempo. Para confirmarlo: capturar `stderr` del subproceso en el mensaje del `assert` y repetir con `-n auto` varias veces | Quien coja una tarea pequeña de tests. Opciones: agruparlos en un solo worker (`@pytest.mark.xdist_group`) o ejecutarlos fuera del paralelo; volcar `stderr` en el fallo; un reintento acotado | Abierto |
| 2026-11-09 | **Riesgo confirmado (prioridad alta).** Analizador de eventos con Claude real; afecta a T1-15 (hecha), a T2-03 (comparte `analyzer.py`) y a los pasos 5 y 6 del guion. No bloquea T2-10 | **Confirmado con `ANTHROPIC_API_KEY` puesta** (replay de los 3 eventos y llamadas directas al analizador): (1) **La dirección del modelo contradice `observed`:** BCE, `RATES_EUR` «baja» (observado: sube) y `EURUSD` «baja» (sube), con una cadena que dice «los tipos de interés del euro bajan» y «el euro pierde atractivo»; NVIDIA, `EQ_GLOBAL` «baja» (observado: sube ligeramente). Petróleo coincide. (2) **Las cifras sí pueden cambiar:** `events/pipeline.py` usa `analysis.channels` para elegir qué factores entran en el `ShockSet` (`selected_by=analyzer`), y el modelo dejó fuera `EQ_US_TECH` en el BCE y todo salvo bolsa y tecnológicas en NVIDIA; el impacto de las carteras deja entonces de ser el de «todos los factores observados». Esto rompe la regla 1 de `CLAUDE.md` en espíritu: el LLM influye en un número. (3) **Timeout:** `_TIMEOUT_S = 4.0` y las llamadas tardan 3,1–4,1 s; BCE y petróleo agotaron los 2 intentos y cayeron en `fallback` y NVIDIA no. Con la clave, la demo alternará entre cadena del modelo y de respaldo según la latencia. (4) Nada valida `channels[].direction` contra el signo de `observed` y `_user_message` solo pasa los **nombres** de los factores. `agent_log` sigue vacía (T2-03). **Arreglo:** T2-26 (ver *Notas para retomar*): cifras siempre con todos los factores observados; dirección observada al prompt y validación; timeout de 10 s; caché del análisis y pre-análisis de NVIDIA | Una tarea nueva, T2-26 (`backend/app/agents/analyzer.py`, `backend/app/agents/prompts/analyzer.md`, `backend/app/events/pipeline.py`, tests). Ojo: T2-03 ya tiene pendiente `analyzer.py` (cambiar `_ORDER` por `guardian.check`); quien coja una no debe pisar la otra | Abierto |
| 2026-11-09 | **Prioridad alta.** Paso 6 del guion (narrativa del BCE); afecta a T0-10 (datos del replay, ya hecha), y de rebote a T2-09 (explicaciones) y T3-07/T3-09 (PDF y ensayos). No bloquea T2-10 | El BCE de Laura sale −89 a −73 € mientras la cadena causal dice que «los bonos y fondos de renta fija tienden a ganar valor». **Diagnóstico: (b), datos correctos y narrativa equivocada, no hay error de signo ni de unidades.** (1) `observed.factors.RATES_EUR` = +0,00024 y `data/factors/RATES_EUR.csv` lo confirma: la rentabilidad pasó de 2,6234 % (4-jun-2025) a 2,6470 % (5-jun), +2,4 pb. Ese día **subió**, aunque el BCE bajara 25 pb (ya estaba descontado). (2) Las betas de `RATES_EUR` de los fondos de renta fija son negativas (Vanguard Euro Gov. −5,92; Global Bond hedged −3,94; Corporate EUR −3,26; R² 0,56–0,78): duración de 3 a 6 años, signo y unidades coherentes. (3) El análisis guardado (`analyzed_model: fallback`) da a `RATES_EUR` la dirección `up` (sale de `observed`, bien), pero su `causal_chain` es la redacción a mano de `fallback_chain` en `data/events/replay/bce-2025-06.json`, que dice «bajan los tipos… la rentabilidad de los bonos en euros» y «bonos… ganan valor». El motor aplica el dato real: rentabilidad al alza × beta negativa = renta fija a la baja. Hay que reescribir esa cadena (y el `text` si lo repite) para que diga que, pese a la bajada del BCE, la rentabilidad de los bonos subió ligeramente y la renta fija cede algo. **Revisadas las otras dos cadenas contra `observed`:** petróleo y NVIDIA coinciden (crudo +7,0 %, bolsa −0,3 %, tipos +2,5 pb con «inflación al alza»; NVDA −8,5 %, tecnológicas −2,8 %). Solo falla el BCE, y en **dos** canales: `RATES_EUR` (+2,4 pb frente a «bajan… la rentabilidad de los bonos») y `EURUSD` (+0,33 %, el euro sube, frente a «el euro puede perder atractivo frente al dólar»). Menor: en NVIDIA la bolsa global sube +0,18 % y la cadena dice que arrastra a «los fondos que las replican» (vale solo para los de tecnología). Javier en «Tranquilo» es correcto (umbral de 900 €) | Quien coja una tarea pequeña sobre `data/events/replay/*.json` (`fallback_chain`); lo escribió Manu en T0-10 | Resuelto: T2-27 en `main` (#77). `fallback_chain` del BCE reescrita (rentabilidad al alza, renta fija cede, euro más fuerte, tecnológicas a la baja) y comprobada contra los impactos de Laura y Javier. Petróleo y NVIDIA no hacían falta. Queda el riesgo del analizador real (T2-26) |
| 2026-11-09 | **Prioridad alta.** Paso 5 y 6 del guion (rangos del impacto); no bloquea T2-10 | Tras `make up` + `/demo/reset` + replay, todos los eventos salían con `low_eur == high_eur` (Laura: NVIDIA −223,69 €; Javier: 0,00 € en BCE y petróleo) y confianza `baja`. **Causa confirmada:** `factor_beta` queda vacía (0 filas) porque `make up` y `make seed` no ejecutan `compute_betas.py` (el servicio `seed` de `docker-compose.yml` solo hace `alembic upgrade head` y `seed_db.py`). Sin betas `impact/engine.py` no suma incertidumbre y el rango se colapsa. Al ejecutar `compute_betas.py` (75 filas) y repetir reset + replay, los rangos se abren y la confianza sube: Laura NVIDIA −349 a −325 €, petróleo −250 a −207 €, BCE −89 a −73 € (alta); Javier NVIDIA −273 a −206 €, petróleo −451 a −352 €, BCE −243 a −206 € (media). Arreglo en la tarea T2-25 (Marcos) | Nadie: lo resuelve T2-25 (el servicio `seed` ejecuta `compute_betas.py` tras `seed_db.py`) | Resuelto: T2-25 en `main` (#72). Tras `down -v` y `up --build`, `factor_beta` tiene 75 filas y los rangos salen abiertos. Quien ya tuviera una BD levantada antes: `make seed` (o `make betas`) |
| 2026-11-08 | Ninguna (tarea menor de setup) | `playwright-cli` no encuentra Chrome en Windows (`chrome.exe` no instalado) y hay que usar `--browser=msedge`. Hay que hacer que `scripts/setup-dev.sh` deje a `playwright-cli` usando su propio Chromium | Quien coja la tarea menor de `scripts/setup-dev.sh` | Abierto |
| 2026-11-09 | Paso 5 del guion (datos de T2-15) | Paso 5 sin oportunidades con el seed actual: Laura solo recibe riesgos en el radar y Javier sale vacío, porque `last_execution_at` de `dca_laura` (2026-11-05) coincide con el último precio. Valor propuesto: 2026-10-05 (−4,01 %). Detalle en *Notas para retomar* (T2-15) | Quien coja T2-15 (ajustar `data/seed/portfolios/laura.json`) | Cerrado: en `main` (#71) |
| 2026-11-09 | Ninguna (mejora de T2-05) | `exposure/templates.py` importa `agents.fact_format`: rompe un poco la regla de hablar solo por `service.py`. Mover el formato a `core/format.py` obliga a tocar `agents/context.py`, que declara T2-09 (🧪 en PR). Se deja como está | Jaime (T2-09): cuando esté en `main`, mover `fact_format` a `core/format.py` y apuntar `agents` y `exposure` ahí | Abierto |
| 2026-11-08 | T0-05 | `EventImpactOut` (T0-04) no está en `main`; `agents` usa `EventImpactStub` | T0-04 (Jaime) | Abierto: sustituir `EventImpactStub` por `schemas.impact.EventImpactOut` al subir T0-04 |

## 6. Peticiones de contrato

Cambios en `backend/app/schemas/` o en endpoints. Los contratos se cierran en la fase 0; después solo se cambian con un PR propio (sin mezclar implementación) y avisando al equipo.

| Fecha/hora | Pide | Esquema / endpoint | Cambio | Afecta a | Estado |
| --- | --- | --- | --- | --- | --- |
| 2026-11-08 | Marcos (T0-07) a Alons (T0-01) | Prefijo de la API | Confirmar que `main.py` monta todos los routers bajo `/api/v1` (`SPEC.md` §11). El cliente del frontend usa la base `/api/v1` y el proxy de Vite reenvía `/api` tal cual | T0-01, T0-03, T0-07 y todo el frontend | Confirmado: `main.py` monta todos los routers de `app/api/` bajo `/api/v1` (D-034); todas las rutas del OpenAPI empiezan por `/api/v1/` (lo comprueba `test_gen_api.py`) |
| 2026-11-08 | Marcos (T0-05) a Jaime (T0-04) | `ExplanationStatus`, `SentenceStatus`, `StatusState`, `StatusFacts` | Importar de `app.schemas.agents` en `schemas/impact.py` y `schemas/status.py` (no redefinirlos). `StatusFacts` es la entrada de `agents.write_status_sentence`; el módulo `status` la rellena | T0-04, T1-17, T2-04 | Pendiente de confirmar |
| 2026-11-08 | Alons (T1-03) al equipo | `AssetOut` (`GET /assets/lookup`), `PriceOut` (`prices.latest`/`history`), `DemoResetRequest`/`DemoResetOut` (`POST /demo/reset`) | Modelos nuevos, sin cambios en los existentes. PR #20 (solo contrato); decisión «Contratos de activo, precio y reset de demo (T1-03)» | T1-02, T1-03, T1-19, T2-03 | Hecho: en `main` (#20) |
| 2026-11-08 | Jaime (T1-15) al equipo | `ReplayRequest` (`POST /demo/replay/{event_id}`) | Modelo nuevo y cuerpo opcional (`occurred_at`, `silent`), definido en el diseño §4.6. PR propio, solo contrato | T1-15, T2-03 | Hecho: en `main` (#30) |
| 2026-11-09 | Alons (T1-04) al equipo | `Money`, `Units`, `Price` (`schemas/common.py`) | Arreglo de serialización: el cero salía como `0E-8`; ahora sale en coma fija (`0.00000000`). No cambia la forma ni el OpenAPI. PR #32 (solo contrato) | T1-04 y cualquier respuesta con importes o participaciones a cero | Hecho: en `main` (#32) |
| 2026-11-09 | Alons (T1-06) al equipo | `GET /portfolios/{id}/dca-executions?status=`, `POST /demo/dca/run` | Ruta nueva para listar las aportaciones de una cartera (`list[DcaExecutionOut]`, `?status=pending` para las pendientes) y respuesta de `/demo/dca/run` (`list[DcaExecutionOut]`). Sin modelos nuevos. PR #34 (solo contrato); D-055 | T1-06, T1-20, T2-08 | Hecho: en `main` (#34) |
| 2026-11-10 | Jaime (T2-03) al equipo | `PUT /demo/clock`, `DemoClockRequest`, `DemoClockOut` | Ruta y modelos nuevos definidos en el diseño §4.6 (la respuesta `{now}` no estaba fijada). Sin cambios en los existentes. PR #76 (solo contrato) | T2-03 | Hecho: en `main` (#76) |
| 2026-11-10 | Marcos (T2-26) al equipo | `EventAnalysis` | Campo opcional nuevo `prompt_version: str \| None = None`: versión del prompt del analizador con el que se hizo el análisis, para que la caché (`event.analysis` ya guardado) se invalide al cambiar el prompt. Añadir un campo opcional es aceptable: no renombra ni quita nada. Se pedirá en un PR propio (solo contrato), antes del código de T2-26; la decisión «Las cifras usan todos los factores observados; el analizador solo redacta (T2-26)» lo recoge | T2-26 y quien lea `EventAnalysis` (`events`, `agents`, frontend generado) | Pendiente: se abrirá al coger T2-26 |
| 2026-11-10 | Jaime (T2-17) al equipo | `GET /portfolios/{id}/ticker`, `TickerOut`, `TickerItemOut` | Ruta y modelos nuevos: último precio de cada posición, cierre anterior y `change_pct` (fracción calculada por el backend, `null` sin cierre anterior o con precio fijo), con `source` y `calc_id`. Sin cambios en los existentes. PR #84 (solo contrato; la ruta responde `UPSTREAM_UNAVAILABLE` hasta la implementación) | T2-17 | En PR (#84) |

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
| Q9 | ¿Entran T2-20 a T2-23 (bandeja de avisos en la app, aviso por movimiento de mercado, marcadores de noticias en la gráfica de la cartera y gráfica por activo)? Amplían F12 (avisos, "Si da tiempo") y T2-18; las noticias siguen viniendo solo del replay. El aviso por correo queda fuera por ahora (solo notificaciones en la app) | Equipo, checkpoint del mar 10 a las 18:00 | Abierta. Si se aceptan: decisión nueva y actualizar `INGENIERIA.md` §4 |

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
