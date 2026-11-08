# Registro de decisiones — KAIROS

Sirve para retomar el trabajo tras un `/clear` o al cambiar de tarea sin repetir discusiones.

## Cómo se usa

- **Solo se añade al final.** No se borra ni se reescribe una entrada; si cambia, se crea una nueva que la sustituye y en la antigua solo se cambia *Estado* a `Sustituida por D-xxx`.
- **IDs correlativos `D-0xx`, asignados por la Action.** Las decisiones nuevas van con `D-XXX` (en la entrada, en la fila del índice y en las referencias desde otros ficheros **del mismo PR**; fuera del PR, p. ej. en el tablero, se cita por título, nunca como `D-XXX`); si metes varias en la misma rama, `D-XXX-a`, `D-XXX-b`… La Action `renumber-decisions` (`scripts/renumber_decisions.py`) las numera al entrar en `main`, por orden de aparición, y actualiza entrada, índice y referencias. No las toques a mano ni renumeres en el PR. Añade siempre al final y actualiza el índice. `docs/decisiones.md` es una excepción a la propiedad por tarea: cualquiera puede añadir.
- **Estados**: `Propuesta` (falta validar con el equipo en el siguiente checkpoint) · `Aceptada` · `Sustituida por D-xxx` · `Descartada`.
- Una decisión merece entrada si: cambia un contrato o el modelo de datos, añade una dependencia, afecta a otro módulo, o la vas a olvidar en 2 horas.
- Plantilla (o usa `/decision`):

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

| ID | Fecha | Título | Estado |
| --- | --- | --- | --- |
| D-001 | 2026-11-08 | Stack: FastAPI + React/TS + PostgreSQL + Docker Compose | Aceptada |
| D-002 | 2026-11-08 | El LLM nunca calcula cifras | Aceptada |
| D-003 | 2026-11-08 | Eventos en modo replay | Aceptada |
| D-004 | 2026-11-08 | Widget simulado en web móvil, sin nativo | Aceptada |
| D-005 | 2026-11-08 | Operaciones como registros, no órdenes | Aceptada |
| D-006 | 2026-11-08 | Monorepo con carpetas por dueño y `service.py` como frontera | Sustituida por D-016 |
| D-007 | 2026-11-08 | Posiciones derivadas de lotes fiscales | Propuesta |
| D-008 | 2026-11-08 | `Decimal` para dinero y participaciones | Propuesta |
| D-009 | 2026-11-08 | Reloj inyectable y replay con fecha de hoy | Sustituida por D-031 |
| D-010 | 2026-11-08 | Guardián determinista, validación frase a frase | Propuesta |
| D-011 | 2026-11-08 | Contexto precargado para la voz | Propuesta |
| D-012 | 2026-11-08 | Modelos y proveedores configurables por `.env` | Aceptada |
| D-013 | 2026-11-08 | Sin login: selector de cartera Laura / Javier | Propuesta |
| D-014 | 2026-11-08 | Modo de datos `offline` por defecto | Propuesta |
| D-015 | 2026-11-08 | Contratos y mocks antes del domingo 8 a las 23:59 | Propuesta |
| D-016 | 2026-11-08 | Modelo de trabajo sin roles: propiedad por tarea y fases (sustituye a D-006) | Aceptada |
| D-017 | 2026-11-08 | Claims de tareas directos a `main` | Aceptada |
| D-018 | 2026-11-08 | Ejemplos JSON como fuente de los mocks | Aceptada |
| D-019 | 2026-11-08 | Proveedor de LLM y voz | Aceptada |
| D-020 | 2026-11-08 | Eventos del replay | Aceptada |
| D-021 | 2026-11-08 | Consenso solo para el BCE | Aceptada |
| D-022 | 2026-11-08 | Umbral de desviación del plan: `drift_threshold` = 0,10 | Aceptada |
| D-023 | 2026-11-08 | F11 y F13 en versión mínima pasan a MVP | Aceptada |
| D-024 | 2026-11-08 | Hito del guion completo: martes 10 a las 18:00 | Aceptada |
| D-025 | 2026-11-08 | Las magnitudes de un evento salen de los datos | Aceptada |
| D-026 | 2026-11-08 | Precios en directo solo con clave de mercado | Aceptada |
| D-027 | 2026-11-08 | El ZIP sin claves de Claude y ElevenLabs | Aceptada |
| D-028 | 2026-11-08 | El paso 1 del guion carga la cartera de ejemplo | Aceptada |
| D-029 | 2026-11-08 | Proyección y agenda en un módulo `planning` | Aceptada |
| D-030 | 2026-11-08 | Año de `DEMO_CLOCK` | Aceptada |
| D-031 | 2026-11-08 | Reloj inyectable y ajuste de demo en la valoración (sustituye a D-009) | Aceptada |
| D-032 | 2026-11-08 | Avisos mínimos (`event_impact`, 2 por semana ISO) pasan a MVP | Aceptada |
| D-033 | 2026-11-08 | Herramientas de Claude Code a nivel de proyecto. Añade (solo desarrollo, no entran en la app): plugin superpowers, skills impeccable / emil-design-eng / review-animations / playwright-cli, y `@playwright/cli` global vía `scripts/setup-dev.sh` | Aceptada |
| D-034 | 2026-11-08 | Esqueleto (T0-01): ficheros extra, servicio `seed` y `calc_trace` en `core` | Aceptada |
| D-035 | 2026-11-08 | Dependencias y base del frontend (T0-07): `react-router`, proxy `/api` sin reescribir, formato único de cifras | Aceptada |
| D-036 | 2026-11-08 | Contrato de cartera (T0-02): peticiones, variantes de ejemplo y mock por API | Aceptada |
| D-037 | 2026-11-08 | `make gen-api` (T0-03): `openapi-typescript` por `npx` con versión fija, tipos raíz y salida en el repo | Aceptada |
| D-038 | 2026-11-08 | Formato de `data/seed` y supuestos de rentabilidad (T0-08) | Propuesta |
| D-039 | 2026-11-08 | Contratos de eventos, agentes y avisos (T0-05): `/events` fuera, `EventImpactStub`, `StatusFacts`, nombres de ejemplos SSE | Aceptada |
| D-040 | 2026-11-08 | Contrato y mock de voz (T0-06): mensajes STT por clase, caché de frases aprobadas y `SENTENCE_NOT_APPROVED` → 404 | Aceptada |
| D-041 | 2026-11-08 | Contrato de impacto y exposición (T0-04): rutas, modelos añadidos y ejemplos | Propuesta |
| D-042 | 2026-11-08 | Modelo de datos y migración inicial (T1-01): tablas de DCA y de ajuste de demo, columnas añadidas y registro `app.models` | Propuesta |
| D-043 | 2026-11-08 | IDs de ElevenLabs (T0-09): Scribe v2 Realtime, Flash v2.5, voz en español y normalización de cifras | Propuesta |
| D-044 | 2026-11-08 | Eventos de replay (T0-10): formato del texto como entrada de fuente | Propuesta |
| D-045 | 2026-11-08 | Históricos y `observed` (T1-09): series de factores, formato CSV y sesión de reacción | Propuesta |
| D-XXX | 2026-11-08 | Contratos de activo, precio y reset de demo (T1-03): `AssetOut`, `PriceOut`, `DemoResetRequest/Out` | Propuesta |
| D-XXX | 2026-11-08 | Precios offline (T1-02): lectura de `data/prices` y `data/factors/EURUSD.csv`, catálogo desde `assets.json` y precios en memoria | Propuesta |

---

### D-001 · Stack: FastAPI + React/TS + PostgreSQL + Docker Compose
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: 4 días, 5 personas, el jurado debe poder ejecutarlo.
- Decisión: backend Python 3.12 + FastAPI; frontend React + TypeScript + Vite; PostgreSQL 16; Docker Compose. Gestores `uv` y `npm`.
- Motivo: Python para pandas/statsmodels y SDKs de Anthropic y ElevenLabs; React para una web móvil que simula el widget; Compose para `docker compose up`.
- Alternativas descartadas: SQLite (menos fiel a la arquitectura del pitch, pero más simple; se puede recuperar si Postgres da guerra); app nativa.
- Consecuencias: ver `SPEC.md` §2.

### D-002 · El LLM nunca calcula cifras
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: una cifra inventada destruye la confianza y la rúbrica premia madurez técnica.
- Decisión: todas las cifras salen de `portfolio` o `impact`; Claude solo redacta a partir de resultados de herramientas; el guardián comprueba que cada número del texto existe en esos resultados.
- Motivo: trazabilidad (principio 6) y argumento para el jurado.
- Consecuencias: herramientas del explicador devuelven valores ya redondeados para mostrar; prompts sin cifras de ejemplo.

### D-003 · Eventos en modo replay
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: la demo no puede depender de que ocurra algo durante la presentación.
- Decisión: 3-4 eventos reales pasados en `data/events/replay/*.json`, reinyectados con `/demo/replay/{id}`.
- Consecuencias: eventos en vivo pasan a "Después" (F16).

### D-004 · Widget simulado en web móvil, sin nativo
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: pregunta abierta del documento de idea; nadie confirmado en Kotlin/Swift.
- Decisión: pantalla de inicio de móvil simulada en la web con el widget como componente React.
- Motivo: el tiempo va a voz, motor e impacto, que es lo que puntúa.
- Consecuencias: F18 queda en "Después".

### D-005 · Operaciones como registros, no órdenes
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Decisión: comprar, vender, traspasar y DCA solo registran en KAIROS; el usuario ejecuta en su bróker.
- Motivo: sin licencia de intermediario; principio "contexto, no órdenes".

### D-006 · Monorepo con carpetas por dueño y `service.py` como frontera
- Fecha: 2026-11-08 · Autor: equipo · Estado: Sustituida por D-016
- Contexto: 5 personas con 5 sesiones de Claude Code en paralelo; riesgo alto de conflictos y de que una IA "arregle" el módulo de otro.
- Decisión: cada carpeta tiene dueño (`TABLERO.md`); los módulos se importan solo vía `service.py`; `schemas/` es contrato compartido y se cambia con PR propio.
- Alternativas descartadas: repos separados (más fricción con Compose y tipos compartidos).
- Consecuencias: CLAUDE.md prohíbe editar carpetas ajenas.

### D-007 · Posiciones derivadas de lotes fiscales
- Fecha: 2026-11-08 · Autor: P1 (propuesta inicial) · Estado: Propuesta
- Contexto: hay que soportar FIFO en ventas y traspasos que conservan coste y antigüedad.
- Decisión: tablas `transaction` (libro, fuente de verdad) y `tax_lot`; la posición se calcula sumando lotes. No hay tabla `position`.
- Motivo: FIFO y traspasos salen naturales; una tabla de posiciones con precio medio pierde la fecha de cada compra.
- Consecuencias: el alta inicial crea un lote por activo con la fecha indicada.

### D-008 · `Decimal` para dinero y participaciones
- Fecha: 2026-11-08 · Autor: equipo · Estado: Propuesta
- Decisión: `Decimal` en Python, `NUMERIC` en BD, `string` en JSON (Pydantic serializa `Decimal` como texto); el frontend formatea con `Intl.NumberFormat('es-ES')`.
- Motivo: evitar errores de redondeo visibles en la demo (p. ej. 0,30000000004 €).
- Consecuencias: pandas solo dentro de `impact/` y se convierte a `Decimal` en la salida.

### D-009 · Reloj inyectable y replay con fecha de hoy
- Fecha: 2026-11-08 · Autor: equipo · Estado: Sustituida por D-031
- Contexto: DCA, estados de 72 h y eventos dependen de la fecha; en la demo hay que controlarla.
- Decisión: `app.core.clock.now()` en todo el backend; `DEMO_CLOCK` y `/demo/clock` la fijan. El replay reinyecta el evento con `occurred_at = now()` y calcula el impacto sobre la valoración actual, sin reescribir precios.
- Consecuencias: prohibido `datetime.now()` (regla de ruff `DTZ`).

### D-010 · Guardián determinista, validación frase a frase
- Fecha: 2026-11-08 · Autor: P3 (propuesta inicial) · Estado: Propuesta
- Contexto: el guardián debe validar todo antes del usuario, pero la voz necesita streaming para < 2 s.
- Decisión: reglas deterministas (patrones prohibidos + comprobación de cifras) aplicadas a cada frase antes de mandarla al TTS. Bloqueo → reintento → plantilla. Verificación extra con LLM solo si `GUARDIAN_LLM_CHECK=true`.
- Alternativas descartadas: validar la respuesta entera antes de hablar (+0,5-1 s); solo LLM (lento y no determinista para tests).
- Consecuencias: si una frase intermedia se bloquea, se corta la respuesta y se completa con plantilla.

### D-011 · Contexto precargado para la voz
- Fecha: 2026-11-08 · Autor: P3 (propuesta inicial) · Estado: Propuesta
- Contexto: cada ronda de tool calling añade ~0,5-1 s.
- Decisión: el prompt del explicador incluye un bloque de contexto con caché (patrimonio, asignación, eventos de 7 días con impacto, estado del plan); las herramientas solo se usan para preguntas fuera de ese contexto.
- Consecuencias: el guardián acepta cifras del bloque de contexto como fuente válida.

### D-012 · Modelos y proveedores configurables por `.env`
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Decisión: `ANTHROPIC_MODEL_FAST` (def. `claude-haiku-5-5`), `ANTHROPIC_MODEL_DEEP` (def. `claude-sonnet-5-5`), IDs de ElevenLabs y proveedor de mercado en `.env`.
- Motivo: poder cambiar por coste o latencia sin tocar código; cierra la pregunta abierta "proveedor de LLM y voz" a falta de medir latencia.

### D-013 · Sin login: selector de cartera Laura / Javier
- Fecha: 2026-11-08 · Autor: equipo · Estado: Propuesta
- Decisión: no hay usuarios; la app tiene un selector oculto (o parámetro `?p=laura`) para cambiar de cartera en el paso 6 de la demo.

### D-014 · Modo de datos `offline` por defecto
- Fecha: 2026-11-08 · Autor: equipo · Estado: Propuesta
- Contexto: cuotas gratuitas bajas y el jurado no tendrá claves de APIs de mercado.
- Decisión: `MARKET_DATA_PROVIDER=offline` usa `data/prices`; los proveedores reales son opcionales.
- Consecuencias: el README solo exige claves de Anthropic y ElevenLabs.

### D-015 · Contratos y mocks antes del domingo 8 a las 23:59
- Fecha: 2026-11-08 · Autor: equipo · Estado: Propuesta
- Decisión: cada módulo publica sus `schemas` y un `mock.py` (y el frontend sus mocks de API) antes del domingo 8 a las 23:59. Desde ahí cada uno trabaja contra mocks hasta que el real esté listo.
- Motivo: que nadie quede bloqueado esperando a otro.

---

<!-- Nuevas decisiones debajo de esta línea. Recuerda añadirlas también al índice. -->

### D-016 · Modelo de trabajo sin roles: propiedad por tarea y fases (sustituye a D-006)
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: 5 personas con 5 sesiones de Claude Code en paralelo. Los roles fijos P1–P5 con carpetas con dueño concentraban la carga y obligaban a esperar a la persona dueña.
- Decisión:
  - No hay roles ni carpetas con dueño: cualquiera hace cualquier tarea.
  - El trabajo se organiza en 4 fases (0 cimientos y contratos · 1 datos y motores · 2 experiencia e integración · 3 endurecer y entregar). Una fase se cierra cuando todas sus tareas están en `main` con `make lint && make test` en verde. Se puede adelantar una tarea de la fase siguiente solo si todas sus dependencias están hechas.
  - Coger una tarea es un commit de claim en `TABLERO.md` antes de empezar. Mientras está en curso, quien la tiene es dueño de los ficheros que declara; no se coge una tarea cuyos ficheros solapen con los de otra en curso.
  - Se mantienen: `service.py` como única frontera entre módulos (regla de arquitectura, no de propiedad); contratos de `backend/app/schemas/` cerrados en la fase 0 y, después, cambiados solo con PR propio y aviso al equipo; las reglas de producto de `CLAUDE.md`.
  - El merge a `main` lo hace quien abre el PR, tras la aprobación de un revisor y con el CI en verde. Qué "Si da tiempo" entra lo decide el equipo en el checkpoint del martes a las 18:00 y se apunta aquí.
- Motivo: reparte la carga, elimina esperas por persona y mantiene el aislamiento entre sesiones donde importa (los ficheros que se están tocando).
- Alternativas descartadas: seguir con carpetas por dueño; cola de tareas sin declaración de ficheros (se pisarían).
- Consecuencias: `CLAUDE.md`, `TABLERO.md`, `SPEC.md` y los comandos `/inicio`, `/cierre`, `/decision` y `/coger` cambian. Los IDs `T-P<n>-<nn>` pasan a `T<fase>-<nn>` (tabla en `TABLERO.md` §9).

### D-017 · Claims de tareas directos a `main`
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: dos personas pueden coger la misma tarea si el claim va por PR.
- Decisión: excepción explícita a "todo por PR". Solo se permiten commits directos a `main` que toquen únicamente `docs/TABLERO.md` y cuyo mensaje sea `docs: claim|release|done T<x>-<nn>`. Flujo: `git pull --rebase` → comprobar que la tarea sigue libre → commit → `git push`; si el push falla, se repite desde el pull.
- Motivo: un claim solo vale si es inmediato y visible para todos.
- Consecuencias: `CLAUDE.md` y `/coger` lo recogen. El repositorio es privado en plan gratuito de GitHub y no admite protección de rama (la API devuelve 403), así que el push directo no está bloqueado y la regla se cumple por convención.

### D-018 · Ejemplos JSON como fuente de los mocks
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: backend y frontend necesitan mocks coherentes con los contratos desde el domingo.
- Decisión: cada esquema tiene un JSON en `backend/app/schemas/examples/<Modelo>.json` con `"illustrative": true`. Un test en CI valida cada ejemplo contra su modelo Pydantic. Esos ejemplos son los mocks del backend (`mock.py` los carga) y del frontend (`make gen-api` los copia a `frontend/src/api/mocks/`, todos los que existan).
- Motivo: una sola fuente; el mock no puede divergir del contrato.
- Consecuencias: tareas T0-02 a T0-06.

### D-019 · Proveedor de LLM y voz
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 4 del diseño del MVP.
- Decisión: Claude (Haiku 5.5 rápido y Sonnet 5.5 profundo, por `.env`) + ElevenLabs (Scribe v2 Realtime y Flash v2.5). Si la medición de latencia (T2-16) falla, se cambia de modelo o de voz, no de proveedor. Confirma D-012.
- Consecuencias: T0-09 verifica los IDs exactos.

### D-020 · Eventos del replay
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 5 del diseño.
- Decisión: (a) BCE 5 jun 2025, bajada de 25 pb, con consenso; (b) petróleo 13 jun 2025, ataque de Israel a Irán y salto del Brent; (c) resultados que hunden a las tecnológicas de EE. UU.: propuesta NVIDIA, resultados del 26 feb 2025 y caída del 27 feb. Se confirman fechas y movimientos con los datos (T0-10, T1-09); si un evento no muestra movimiento claro, se cambia por otro del mismo tipo. Opcional: un día de dólar débil.
- Consecuencias: cierra Q5.

### D-021 · Consenso solo para el BCE
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 6 del diseño.
- Decisión: solo el BCE lleva consenso de mercado citado en prensa, guardado en el JSON del evento. En los demás, `consensus: null` y `surprise: null`.
- Consecuencias: cierra Q6.

### D-022 · Umbral de desviación del plan: `drift_threshold` = 0,10
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: Laura (RV 76 %, objetivo 70 %) arrancaba en "Revisa tu plan" con el umbral de 5 pp, pero el paso 1 del guion la quiere en "Tranquilo". `SPEC.md` usaba `drift_threshold_pp` y el diseño, la fracción 0,10.
- Decisión: el campo se llama `drift_threshold`, es una **fracción** y vale 0,10 por defecto. 76 % frente a 70 % da Tranquilo; el ejemplo del producto (82 % frente a 70 %) sigue dando "Revisa tu plan". No se cambia ni el producto ni la cartera.
- Consecuencias: `SPEC.md` (§6, §8.5, §8.6, §13) y los contratos usan `drift_threshold`. Cierra Q3.

### D-023 · F11 y F13 en versión mínima pasan a MVP
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: el paso 7 ("¿Voy bien?") depende de F11 y el paso 2 (radiografía) de F13, ambas "Si da tiempo".
- Decisión: pasan a MVP solo la parte mínima: plan + proyección (`ProjectionOut`) y el bloque `radiography` de `ExposureOut`. El resto sigue en "Si da tiempo".
- Consecuencias: RF-22 y la radiografía (RF-09) pasan a M en `INGENIERIA.md`. Cierra Q4.

### D-024 · Hito del guion completo: martes 10 a las 18:00
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: el producto dice 18:00 y la versión anterior del tablero decía 23:00.
- Decisión: el guion completo funciona en `main` el martes a las 18:00. La regla de recorte del martes a las 15:00 se mantiene. En el checkpoint de las 18:00 el equipo decide qué "Si da tiempo" entra y lo apunta aquí.
- Consecuencias: `TABLERO.md` e `INGENIERIA.md` corregidos.

### D-025 · Las magnitudes de un evento salen de los datos
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 11 del diseño; regla 1 de `CLAUDE.md`.
- Decisión: las magnitudes de los shocks salen del campo `observed` del JSON del replay. El LLM clasifica el evento, elige canales y redacta la cadena causal. `events` construye un `ShockSet` determinista; si el analizador falla, se usan todos los factores observados.

### D-026 · Precios en directo solo con clave de mercado
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 12 del diseño.
- Decisión: con `MARKET_DATA_API_KEY`, el proveedor real refresca acciones y ETF cada 60 s; sin clave (jurado), modo offline con "precio a fecha X". Complementa D-014.

### D-027 · El ZIP sin claves de Claude y ElevenLabs
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 13 del diseño.
- Decisión: las claves son necesarias para la IA (el README las pide en `.env.example`). Sin claves la app arranca: el explicador responde con plantillas construidas con datos del motor (`fallback_used: true`) y no hay audio. No hay respuestas pregrabadas.

### D-028 · El paso 1 del guion carga la cartera de ejemplo
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 14 del diseño.
- Decisión: el guion carga la cartera de ejemplo. El alta por ISIN (F1) se construye igual, pero no está en la ruta crítica del martes a las 18:00.

### D-029 · Proyección y agenda en un módulo `planning`
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 15 del diseño; la proyección y la agenda estaban en el camino crítico del motor de impacto.
- Decisión: viven en `backend/app/planning/` (T1-14, T2-06) y llaman a `impact` y `exposure` solo vía `service.py`. Los endpoints `/projection` y `/agenda` son de ese módulo.

### D-030 · Año de `DEMO_CLOCK`
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 16 del diseño.
- Decisión: 2026 (fechas actuales). `data/prices` llega hasta la fecha de descarga; los eventos son de 2025 y solo aportan `observed`.

### D-031 · Reloj inyectable y ajuste de demo en la valoración (sustituye a D-009)
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: DCA, estados de 72 h y eventos dependen de la fecha. Además, D-009 decía que el replay se calcula "sin reescribir precios"; el equipo decidió que en modo demo el patrimonio mostrado sí refleje el evento (decisión 17 del diseño).
- Decisión:
  - Sigue vigente de D-009: `app.core.clock.now()` en todo el backend; `DEMO_CLOCK` y `/demo/clock` la fijan; prohibido `datetime.now()` (regla de ruff `DTZ`); el replay reinyecta el evento con `occurred_at = now()` y calcula el impacto sobre la valoración actual.
  - Nuevo: **solo con `DEMO_MODE=true`**, la valoración suma el impacto central estimado de cada posición, con la etiqueta "Estimación tras el evento" y su `calc_id` (`demo_adjustments` en `PortfolioOut`). Los precios no se tocan: el ajuste va aparte y se borra en `/demo/reset`.
- Consecuencias: T2-02 implementa `apply_demo_adjustment`. `change_week_*` y `by_asset` de `explain_move` lo incluyen.

### D-032 · Avisos mínimos (`event_impact`, 2 por semana ISO) pasan a MVP
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: RF-23 era "S" en `INGENIERIA.md`, pero el paso 3 del guion (replay → Atento + aviso) y T2-08 dependen de los avisos de tipo `event_impact`.
- Decisión: RF-23 pasa a M en versión mínima: avisos `kind=event_impact` con `score = |impact_eur| / max(150, 0,005 · total)`, aviso si `score ≥ 1`, y límite de 2 por semana ISO y cartera según `clock.now()`. `dca_pending` y `drift` siguen en "Si da tiempo". Contrato en el diseño §4.4.
- Consecuencias: `INGENIERIA.md` (RF-23 y trazabilidad del paso 3) actualizado; T2-08 es MVP.

### D-033 · Herramientas de Claude Code a nivel de proyecto
- Fecha: 2026-11-08 · Autor: Marcos · Estado: Aceptada
- Contexto: cinco sesiones de Claude Code en paralelo; conviene que todas tengan las mismas skills y plugins sin instalar nada a mano.
- Decisión: versionar en git `.claude/settings.json` (plugin `superpowers@claude-plugins-official`, que está en el marketplace oficial, y permisos `allow` de `playwright-cli`, `make`, `uv`, `npm run` y `git pull`), `.claude/skills/` y `skills-lock.json` con las skills `impeccable`, `emil-design-eng`, `review-animations` y `playwright-cli`. Del repo de Emil Kowalski solo esas dos skills (cada skill gasta contexto en cada turno; `emilkowalski/skill` y `emilkowalski/skills` tienen el mismo contenido). `scripts/setup-dev.sh` instala el binario `@playwright/cli` y su navegador (idempotente).
- Motivo: reproducibilidad entre sesiones con un solo paso tras el pull.
- Dependencias de desarrollo que añade: plugin superpowers; skills impeccable, emil-design-eng, review-animations, playwright-cli; paquete npm global `@playwright/cli` (fuera del repo, distinto de `@playwright/test` de T3-02). Ninguna entra en el código de producción.
- Consecuencias: `.claude/.gitignore` y `.playwright-cli/.gitignore` ignoran `settings.local.json` y la salida de playwright-cli, para no tocar el `.gitignore` raíz (de T0-01); cuando T0-01 cierre se pueden mover allí. impeccable puede activar un hook de diseño por edición con `impeccable hooks on`, que escribe en `settings.local.json` (no versionado); no está activado.

### D-034 · Esqueleto (T0-01): ficheros extra, servicio `seed` y `calc_trace` en `core`
- Fecha: 2026-11-08 · Autor: Alons · Estado: Aceptada
- Contexto: T0-01 necesitaba ficheros que su fila no declaraba y había que decidir dónde vive la tabla de trazas.
- Decisión:
  - Ficheros añadidos fuera de la lista de T0-01: `.gitattributes` (LF en todo el repo; con CRLF fallan los `sh -c` de Compose en Windows), `backend/Dockerfile`, `backend/.dockerignore`, `backend/uv.lock`, `backend/app/api/{__init__,health}.py` y los tests `backend/tests/test_{core_clock,core_errors,core_trace,schemas_common,main}.py`. Ninguna otra tarea los declara.
  - `main.py` descubre solo los módulos de `app/api/`: cada uno exporta `router` y se monta en `/api/v1`. Para añadir un router no hay que tocar `main.py`.
  - Compose tiene un servicio `seed` (imagen del backend) que corre en cada `up` antes del backend: `alembic upgrade head` si existe `alembic.ini` y `python /scripts/seed_db.py` si existe. Por eso **`seed_db.py` (T1-03) tiene que ser idempotente**. `data/` y `scripts/` se montan en `/data` y `/scripts` (solo lectura).
  - El modelo `CalcTrace` (tabla `calc_trace`) vive en `core/trace.py`, junto a `record()` y `get()`. Lleva además `formula` y `parent_calc_ids`, que pide `TraceOut`. T1-01 debe incluirlo en la migración inicial (importando `app.core.trace`).
  - `frontend/Dockerfile` construye con Vite si hay `package.json` y, si no, sirve una página provisional. nginx reenvía `/api` al backend con SSE y WebSocket. `make test` y `make lint` se saltan el frontend mientras no exista `package.json`.
  - Los tests usan SQLite temporal (`db` fixture en `conftest.py`); nunca Postgres ni APIs externas.
  - Los ejemplos de `schemas/examples/` llevan `"illustrative": true`, pero `ContractModel` rechaza campos extra: quien carga un ejemplo (tests, `mock.py`) quita esa marca antes de validar.
- Dependencias que añade (ya previstas en `SPEC.md` §2/§3): `pydantic-settings`, `psycopg[binary]`; en desarrollo `httpx` (para `TestClient`). Herramientas: imagen `ghcr.io/astral-sh/uv:0.13.7`, `postgres:16-alpine`, `node:22-alpine`, `nginx:1.27-alpine`.
- Consecuencias: T1-01 incluye `calc_trace`; T1-03 hace `seed_db.py` idempotente; T0-07 conviene que añada `frontend/.dockerignore` con `node_modules`.

### D-035 · Dependencias y base del frontend (T0-07)
- Fecha: 2026-11-08 · Autor: Marcos · Estado: Aceptada
- Contexto: T0-07 monta `frontend/`. React, Vite, TypeScript, Tailwind, TanStack Query, Recharts, openapi-typescript y vitest ya estaban aceptados (D-001 / `SPEC.md` §2); aquí solo se anota lo nuevo.
- Decisión:
  - Router: `react-router` (v8). Son 4 rutas simples; no hay motivo para TanStack Router.
  - Tests: `@testing-library/react` y `jsdom` para vitest.
  - Lint: `eslint`, `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh` y `globals`.
  - Sin librerías de componentes ni de iconos. Fuentes del sistema, sin fuentes remotas (la demo funciona sin red).
  - Proxy de Vite: el frontend llama a `/api/...` y Vite lo reenvía al backend **tal cual**, sin quitar el prefijo. La API vive bajo `/api/v1` (`SPEC.md` §11) y `src/api/client.ts` usa `/api/v1` como base; las rutas sin prefijo del diseño son abreviaturas. Pendiente de confirmar con T0-01 que el backend monta los routers en `/api/v1` (*Peticiones de contrato*). Destino por `KAIROS_API_PROXY`: `http://localhost:8000` fuera de Docker, `http://backend:8000` dentro.
  - Formateo de cifras solo con `src/lib/format.ts` (`Intl.NumberFormat('es-ES')`): los importes entran como string Decimal y no se convierten a `number`.
- Consecuencias:
  - Las versiones instaladas son las últimas: React 19 y Tailwind 4 (tokens en `@theme` de `src/index.css`). `SPEC.md` §2 actualizado en el mismo PR.
  - El `Makefile` de T0-01 puede llamar a `npm run lint|typecheck|test|build` en `frontend/`.
  - Tokens y reglas visuales en `DESIGN.md` (raíz); contexto de producto en `PRODUCT.md`.

### D-036 · Contrato de cartera (T0-02): peticiones, variantes de ejemplo y mock por API
- Fecha: 2026-11-08 · Autor: Alons · Estado: Aceptada
- Contexto: el diseño §4.1 define las respuestas, pero no todos los cuerpos de petición. Los contratos se cierran en la fase 0 y `make gen-api` (T0-03) solo ve en el OpenAPI los modelos que usa alguna ruta.
- Decisión:
  - `schemas/portfolio.py` añade modelos que el diseño no nombraba: `PortfolioSummaryOut` (`GET /portfolios`), `PositionsInitRequest` (`POST /positions`), `PlanUpdateRequest` (`PUT /plan`), `DcaPlanCreateRequest`, `DcaPlanUpdateRequest` (`PATCH /portfolios/{id}/dca-plans/{plan_id}`) y `DcaExecutionActionRequest`. `TransactionOut.type` admite `buy`, `sell`, `transfer` y `dca_buy`. En un traspaso, `asset_id` es el fondo de origen y `to_asset_id` (opcional) el de destino. `day` del DCA va de 1 a 28 (día ISO de la semana si es semanal). Que Σ weight sea 1 lo valida el servicio (`DCA_ALLOCATION_INVALID`), no el esquema.
  - Ejemplos: `<Modelo>.json` o `<Modelo>.<variante>.json` (p. ej. `PortfolioOut.javier.json`, `TransactionOut.transfer.json`, `ErrorOut.transfer_not_allowed.json`). Las respuestas van **completas**, como las emite la API (con `null` y `[]`), para que los mocks del frontend coincidan con el backend; las `*Request` pueden omitir campos opcionales. `tests/test_schema_examples.py` valida **todos** los ejemplos de cualquier tarea buscando el modelo por nombre en `app.schemas.*`, y comprueba que el JSON coincide con su volcado.
  - `app/schemas/examples/__init__.py` ofrece `load(name)`, que quita `illustrative`. Los `mock.py` de T0-04, T0-05 y T0-06 pueden usarlo.
  - `api/portfolio.py` expone ya todas las rutas de cartera sobre el mock, también las de escritura (devuelven el ejemplo). `POST /dca-executions/{id}` vive ahí de momento; T1-06 puede moverlo a `api/dca.py`. Las escrituras pasan por `portfolio/service.py`, no por el mock.
  - Ficheros añadidos fuera de la fila de T0-02: `backend/app/portfolio/__init__.py`, `backend/app/schemas/examples/__init__.py` y `backend/tests/test_portfolio_mock.py`.
- Consecuencias: T0-03 copia también las variantes. T1-03 a T1-07 sustituyen las funciones de `service.py` sin cambiar sus firmas. Las cifras de los ejemplos usan los activos del seed de T0-08, pero son ilustrativas: con esos precios, la RV de Laura en el mock sale en 0,72, no en 0,76.

### D-037 · `make gen-api` (T0-03): `openapi-typescript` por `npx` con versión fija, tipos raíz y salida en el repo
- Fecha: 2026-11-08 · Autor: Alons · Estado: Aceptada
- Contexto: T0-03 tiene que generar los tipos TS desde el OpenAPI del backend. `openapi-typescript` estaba aceptado (D-001 / `SPEC.md` §2), pero la última versión (7.13.0) pide `typescript@^5` como peer y el frontend usa TypeScript 6 (D-035): `npm install` falla con `ERESOLVE`.
- Decisión:
  - `scripts/gen_api.py` llama a `npx --yes openapi-typescript@7.13.0`, con la versión fija y sin añadirlo a `package.json`. npx lo instala aparte, con su propio TypeScript 5. Así no hace falta `--legacy-peer-deps` en el frontend.
  - Salida en `frontend/src/api/generated/`: `openapi.json` (volcado determinista de `create_app().openapi()`) y `schema.ts`, generado con `--root-types --root-types-no-schema-prefix --alphabetize`. Cada esquema se puede importar por su nombre: `import type { PortfolioOut } from "./generated/schema"` (desde `src/api/`). Todo con LF.
  - `frontend/src/api/mocks/` se **vacía y se rellena** con todos los `schemas/examples/*.json`, variantes incluidas y con `illustrative` intacto. Se copian también los ejemplos sin ruta todavía (p. ej. `TraceOut`), aunque su tipo no salga en `schema.ts` hasta que haya un endpoint que lo use.
  - Lo generado **va al repo**. CI, Docker y quien solo toque el frontend no necesitan ni Python ni npx. Quien cambie un esquema o un ejemplo ejecuta `make gen-api` y sube el resultado en el mismo PR. Sin Node: `make gen-api GEN_API_ARGS=--skip-ts`.
  - Ficheros añadidos fuera de la fila de T0-03: `backend/tests/test_gen_api.py` (copia de mocks y OpenAPI determinista, sin npx) y `frontend/src/api/mocks.test.ts` (el frontend importa los mocks con los tipos generados).
- Consecuencias: T0-04, T0-05 y T0-06 ejecutan `make gen-api` en su PR para que sus tipos y mocks lleguen al frontend. Si sale una versión de `openapi-typescript` compatible con TS 6, se puede pasar a `devDependencies`.

### D-038 · Formato de `data/seed` y supuestos de rentabilidad (T0-08)
- Fecha: 2026-11-08 17:23 · Autor: Jaime · Estado: Propuesta
- Contexto: T0-08 tenía que crear los datos de semilla, pero ningún documento fijaba su formato ni de dónde salen las rentabilidades de la proyección.
- Decisión:
  - `assets.json` lleva `illustrative`, `as_of`, `ter_sources` y `assets`, con las columnas de la tabla `asset` (`SPEC.md` §6). El `id` es el ISIN; el depósito y el plan de pensiones, sin ISIN, usan `DEP-12M` y `PP-MIXTO`.
  - `price_source` es `yahoo:<símbolo>` o `fixed:<valor>` (precio fijo, sin histórico ni betas).
  - `portfolios/<id>.json` lleva `illustrative`, `id`, `name`, `profile`, `base_currency`, `plan`, `dca_plans` y `positions`. Cada posición tiene `asset_id` y `lots` (`acquired_at`, `units`, `cost_eur_per_unit`), que se corresponden con `tax_lot`. Los decimales van como cadenas.
  - Las participaciones se calcularon con los precios de Yahoo del 5-6 de noviembre de 2026 y los costes, con el cierre real de cada fecha de compra. Las carteras son ilustrativas.
  - El DCA de Laura invierte en dos fondos (`IE00B03HD191` 70 % e `IE00B18GC888` 30 %) y no en IWDA como el ejemplo del contrato, porque el producto dice que invierte en "dos fondos indexados".
  - `assumptions.json` toma el escenario `base` de Amundi CMA de abril de 2026, p. 18 (rentabilidad geométrica a 10 años: World 6,7 %, Euro Aggregate 3,5 %, Euro cash 1,8 %). `pesimista` y `optimista` son la base menos o más media desviación típica del rendimiento anualizado a 10 años (volatilidad simulada / √10 / 2). `mixed` es la media simple de `equity` y `fixed_income`.
- Motivo: Amundi es la única fuente primaria localizada con renta variable, renta fija y liquidez en la misma tabla y con las clases en euros. Con esta regla, Laura alcanza su meta de 150.000 € en el escenario base y no en el pesimista, como en el ejemplo del contrato.
- Alternativas descartadas: Vanguard Outlook 2026 (sin cifras en euros y sin rango primario para bonos); J.P. Morgan LTCMA y Fidelity CMA (no se pudo descargar el documento para contrastar la tabla); el tipo de depósito del BCE como rentabilidad de la liquidez (no es una previsión a 10 años).
- Consecuencias:
  - T1-03: `seed_db.py` lee este formato y crea los lotes.
  - T1-02, T1-09 y T1-12: tratan `fixed:<valor>` sin histórico ni betas; T1-09 puede usar el símbolo de `price_source`.
  - T1-14: lee `scenarios` y pondera por la asignación objetivo. Las rentabilidades son brutas, en divisa local y sin efecto divisa en la renta variable global.
  - T2-15: revisa las filas de §5 con el motor real; la fila 2 depende de T1-08.

### D-039 · Contratos de eventos, agentes y avisos (T0-05)
- Fecha: 2026-11-08 · Autor: Marcos · Estado: Aceptada
- Contexto: el diseño §4.2 y §4.4 define estos contratos pero deja cabos sueltos: dónde vive `GET /portfolios/{id}/events`, qué entra en `write_status_sentence` y cómo se nombran los ejemplos de una unión SSE.
- Decisión:
  - `GET /portfolios/{id}/events` es de impacto (T0-04, `SPEC.md` §11) y devuelve `EventImpactOut`. `api/events.py` solo monta el control de replay: `POST /demo/replay/{event_id}` → `ReplayOut {event_id, portfolios: {laura: calc_id, javier: calc_id}, elapsed_ms}`; con `DEMO_MODE=false` responde 403 `DEMO_MODE_DISABLED`.
  - `EventImpactStub` (en `schemas/agents.py`) es provisional: solo los campos que necesitan `write_event_explanation` y `write_alert_message`, sin ejemplo propio y con otro nombre para no chocar con `EventImpactOut` de T0-04. Se sustituye por `schemas.impact.EventImpactOut` cuando T0-04 esté en `main`.
  - `StatusFacts` (entrada de `write_status_sentence`) lleva `state`, `total_eur`, `change_week_pct`, `reason {kind, event_id}` y `calc_id`, más opcionales ya calculados: `event_title`, `top_asset_class`, `main_channel`, `event_impact_eur` (para `atento`) y `equity_current`, `equity_target` (para `revisa_plan`). El LLM no opera con ellos.
  - `ExplanationStatus`, `SentenceStatus` y `StatusState` viven en `schemas/agents.py`; T0-04 los importa de ahí.
  - Unión SSE: `AskEvent` es una unión discriminada por `type` (alias, no clase). Los ejemplos van por clase concreta (`AskMetaEvent.json`, `AskSentenceEvent.json`, `AskSentenceEvent.impact.json`, `AskDoneEvent.json`, `AskErrorEvent.json`) para que el test genérico los encuentre sin cambios.
  - `EventIn.observed` es opcional porque T0-10 escribe los JSON antes de que T1-09 calcule `observed`. `EventAnalysis` rechaza dígitos en `entities[].name`, `channels[].label|rationale`, `companies[].name` y `causal_chain`; los identificadores (`event_id`, `analyzed_model`, claves) pueden llevarlos.
  - `/ask` mock emite `text/event-stream` real (un `data: {...}` por evento, separados por línea en blanco). La cartera inexistente falla con 404 JSON **antes** de abrir el stream.
  - Ficheros añadidos fuera de la fila de T0-05: `backend/app/{agents,events,alerts}/__init__.py` y `backend/tests/test_event_agent_examples.py`. Lo regenerado por `make gen-api` (`frontend/src/api/{generated,mocks}/`) va en el mismo PR, como pide la decisión de `make gen-api` (T0-03).
- Consecuencias: T1-15 y T1-17 sustituyen `mock.py` sin cambiar firmas. Los textos de los mocks de redacción no llevan cifras.

### D-040 · Contrato y mock de voz (T0-06): mensajes STT por clase, caché de frases aprobadas y `SENTENCE_NOT_APPROVED` → 404
- Fecha: 2026-11-08 · Autor: Alons · Estado: Aceptada
- Contexto: el diseño §4.5 define los mensajes de `WS /voice/stt` y `POST /voice/tts`, pero no cómo se modelan ni qué hace el mock. Además `core/errors.py` (T0-01) asignaba 403 a `SENTENCE_NOT_APPROVED`, mientras que el diseño §4.5 y `SPEC.md` §10 dicen 404.
- Decisión:
  - `SENTENCE_NOT_APPROVED` pasa a **404** en `core/errors.py`, como dice el contrato.
  - `schemas/voice.py`: `SttStartMessage` (`sample_rate`, `encoding` y `language` son literales fijos: 16000, `pcm_s16le`, `es`), `SttStopMessage`, `SttPartialMessage`, `SttFinalMessage`, `SttErrorMessage` (`code` es `str`, como en `ErrorOut`) y `TtsRequest {turn_id, index ≥ 0}`, que rechaza campos extra: el cliente nunca manda texto. Uniones discriminadas por `type`: `SttClientMessage` y `SttServerMessage` (alias, como `AskEvent` de T0-05). Un ejemplo por clase concreta, más `ErrorOut.sentence_not_approved.json`.
  - FastAPI no documenta WebSockets, así que los `Stt*Message` no salen en `schema.ts`. `make gen-api` copia sus ejemplos a `frontend/src/api/mocks/`, y T2-14 escribe sus tipos TS en `frontend/src/voice/` a partir de ellos.
  - `voice/service.py`: `register_approved(turn_id, index, text)` (la única función para otros módulos), `reset()`, `get_approved`, `synthesize`, `disclaimer` y `transcribe`. La caché de frases aprobadas es real, no mock: está en memoria, con lock, una clave `(turn_id, index)`, TTL de 5 min con `clock.now()` y limpieza de entradas caducadas en cada acceso. `synthesize` comprueba la caché **antes** de abrir el stream (404 JSON, no audio vacío).
  - `voice/mock.py`: el STT ignora el audio y responde `partial` con el primer frame y `final` al recibir `stop` (los textos de los ejemplos). El TTS devuelve `data/voice/mock.mp3` en trozos de 16 KB. `/voice/disclaimer` sirve `data/voice/disclaimer.mp3` si existe (T1-21) y, si no, `mock.mp3`. La ruta a `data/` se resuelve desde el propio fichero (`parents[3]`): en local da la raíz del repo y en Docker `/data` (montado en Compose).
  - `WS /voice/stt`: si el primer mensaje no es un `start` válido o llega un texto que no es `stop`, el servidor manda `error` `VALIDATION_ERROR` y cierra. Si falla la transcripción, `error` `UPSTREAM_UNAVAILABLE` (el frontend pasa al plan B).
  - `mock.mp3` (6,7 s, 48 kbps mono) se generó en local con la voz es-ES de Windows (Helena) y ffmpeg. Dice: "Audio de prueba de KAIROS. Soy una inteligencia artificial y esto no es asesoramiento financiero.", para que también valga como aviso de IA mientras no exista `disclaimer.mp3`. No lleva cifras.
  - Ficheros añadidos fuera de la fila de T0-06: `backend/app/voice/__init__.py`, `backend/tests/test_voice.py` y `backend/app/core/errors.py` (solo el estado HTTP de `SENTENCE_NOT_APPROVED`). Lo regenerado por `make gen-api` va en el mismo PR.
- Consecuencias: T1-17 (`agents`) llama a `voice.service.register_approved` con cada frase aprobada antes de emitir el evento `sentence`. T1-21 cambia `transcribe`, `synthesize` y `disclaimer` a ElevenLabs sin cambiar firmas, y genera `disclaimer.mp3`. T2-03 llama a `voice.service.reset()` desde `/demo/reset` y borra `voice/mock.py`. T2-14 tipa los mensajes del WebSocket desde los mocks.

### D-041 · Contrato de impacto y exposición (T0-04): rutas, modelos añadidos y ejemplos
- Fecha: 2026-11-08 · Autor: Jaime · Estado: Propuesta
- Contexto: §4.3 define las respuestas, pero no en qué módulo de `api/` vive cada ruta ni el cuerpo de los escenarios.
- Decisión:
  - Rutas: `api/impact.py` sirve `GET /portfolios/{id}/events`, `POST /portfolios/{id}/scenarios` y `GET /portfolios/{id}/move`; `api/exposure.py`, `/exposure` y `/radar`; `api/status.py`, `/status`; `api/planning.py`, `/projection` y `/agenda`. T2-05, T2-06 y T2-07 pueden mover las suyas a `api/{radar,agenda,move}.py`.
  - `schemas/impact.py` añade `ScenarioRequest`, que el diseño solo describía con un JSON. `EventType` y `MovePeriod` son `Literal` para no chocar en el OpenAPI con los enums de T0-05.
  - `ExplanationStatus`, `SentenceStatus`, `StatusState` y `StatusReasonKind` se importan de `schemas/agents.py` (D-039).
  - Los mocks comprueban que la cartera existe con `portfolio.service.get_valued` (404).
  - Ejemplos con los activos y el total de `PortfolioOut.json` (ilustrativos), con desgloses que suman. Variantes: `EventImpactOut.nvda` (sin consenso, `pending`), `StatusOut.tranquilo`, `StatusOut.revisa_plan` y `AgendaItemOut.dca`.
  - Tres diferencias con los JSON de §4.3, que son ilustrativos: en el evento del BCE, `low_eur` es negativo, porque con `low_eur > 0` y más del 50 % en renta fija (por debajo de objetivo) la regla daría `oportunidad`, no `neutral`; `StatusOut.reason.event_impact_eur` es `-470.00`, igual que `by_event` de `MoveAttributionOut`, y no `-514.00`, que es el cambio semanal total; y el título de `cheaper_contribution` evita la palabra "compra" (regla de producto 2).
  - Ficheros añadidos fuera de la fila de T0-04: `backend/app/{impact,exposure,status,planning}/__init__.py` y `backend/tests/test_analysis_mocks.py`.
- Consecuencias: `EventImpactStub` (`schemas/agents.py`) ya se puede sustituir por `EventImpactOut` (D-039).

### D-042 · Modelo de datos y migración inicial (T1-01): tablas de DCA y de ajuste de demo, columnas añadidas y registro `app.models`
- Fecha: 2026-11-08 19:00 · Autor: Alons · Estado: Propuesta
- Contexto: `SPEC.md` §6 no tenía tablas para las ejecuciones de DCA (`DcaExecutionOut`, estado `pending`) ni para el ajuste de demo (D-031), y le faltaban columnas que piden los contratos. Además, las tablas tienen claves foráneas entre módulos y hay que cargarlas todas juntas antes de crear el esquema.
- Decisión:
  - Tablas nuevas: `dca_execution` (id, dca_plan_id, scheduled_for, status, created_at, resolved_at), `dca_execution_line` (execution_id, asset_id, amount_eur, price, price_at, units_estimated, transaction_id) y `demo_adjustment` (portfolio_id, event_id, asset_id, impact_eur, label, calc_id, created_at), **una fila por posición**, para que `value_eur` de cada posición pueda sumar su parte. `PortfolioOut.demo_adjustments` las agrega por evento. Las tres van en `portfolio/models.py`.
  - Columnas añadidas a las de §6: `portfolio.created_at`; `transaction.price_currency`, `realized_gain_eur` y `calc_id`; `tax_lot.units_initial`; `dca_plan.last_execution_at` y `next_execution_at` (vienen en el seed, D-038); `event.text` y `created_at`; `event_impact.impact_pct`, `explanation_status` y `created_at`; `agent_log.created_at`. `agent_log.guardian_verdict` es JSON.
  - IDs de texto que genera cada servicio (`laura`, el ISIN, `dca_laura`, `tx_…`, `lot_…`); solo `demo_adjustment` y `agent_log` usan entero autoincremental. Los enums se guardan como texto con los valores de `app.schemas`, sin tipos `ENUM` de Postgres.
  - Tipos: euros `NUMERIC(18,2)`; participaciones, precios, tipos de cambio, coste por unidad y estadísticos (`beta`, `r2`, `score`, `impact_pct`) `NUMERIC(20,8)`; pesos y fracciones `NUMERIC(10,8)`; fechas `TIMESTAMP WITH TIME ZONE`. Los `calc_id` no llevan clave foránea a `calc_trace`, porque la traza se escribe en su propia sesión.
  - `app/models.py` importa todos los `models.py`; lo usan `alembic/env.py` y el fixture `db` (`conftest.py`). Quien añada un `models.py` lo registra ahí y crea una migración (`alembic revision --autogenerate`, desde `backend/`). `test_migrations.py` falla si los modelos y las migraciones no coinciden.
  - `alembic.ini` en `backend/` (la condición del servicio `seed` de Compose, D-034); la URL sale de `DATABASE_URL`. Migración inicial `0001`, probada en SQLite y en Postgres 16 (subir, `alembic check`, bajar).
  - Ficheros añadidos fuera de la fila de T1-01: `backend/alembic.ini`, `backend/app/models.py`, `backend/app/prices/__init__.py`, `backend/tests/test_migrations.py`, una línea en `backend/tests/conftest.py` y `known-third-party = ["alembic"]` en `backend/pyproject.toml` (ruff tomaba `backend/alembic/` por el paquete).
- Motivo: así T1-06 (DCA) y T2-02 (ajuste de demo) no necesitan otra migración, que podría chocar con las de otras tareas en paralelo.
- Alternativas descartadas: el ajuste de demo agregado por evento (no basta para `value_eur` por posición); `ENUM` de Postgres (cada valor nuevo exigiría una migración y no funcionan igual en SQLite).
- Consecuencias: T1-02, T1-03, T1-06, T1-11, T1-12, T1-13, T1-15, T2-02 y T2-08 ya tienen sus tablas. Si una tarea cambia un modelo, añade una migración `0002_…` encadenada a la última que haya en `main`; si dos ramas crean migraciones a la vez, la segunda en entrar ajusta su `down_revision`. `SPEC.md` §6 actualizado.

### D-043 · IDs de ElevenLabs (T0-09): Scribe v2 Realtime, Flash v2.5, voz en español y normalización de cifras
- Fecha: 2026-11-08 · Autor: Marcos · Estado: Propuesta
- Contexto: `SPEC.md` §2 dejaba sin fijar los IDs exactos de los modelos de voz. T1-21 y T0-06 los necesitan para `.env`. Los IDs se verificaron en la documentación oficial y el resto con llamadas reales a la API (clave en `.env`, ignorado por git).
- Decisión (verificado en la documentación):
  - `ELEVENLABS_STT_MODEL=scribe_v2_realtime`. Va por WebSocket: `wss://api.elevenlabs.io/v1/speech-to-text/realtime?model_id=scribe_v2_realtime`. Auth: cabecera `xi-api-key` desde el backend (la clave no sale del backend) o `token` de un solo uso. Parámetros útiles: `audio_format` (`pcm_16000` por defecto), `language_code` (ISO 639-1 o 639-3), `commit_strategy` (`manual`, `vad`, `turn_prediction`). El cliente envía `input_audio_chunk` con `audio_base_64`, `commit` y `sample_rate`; el servidor responde `session_started`, `partial_transcript` y `committed_transcript`, entre otros. La documentación da una mediana de ~150 ms hasta la transcripción confirmada.
  - `ELEVENLABS_TTS_MODEL=eleven_flash_v2_5`. Latencia nominal de ~75–100 ms (mediana, sin red ni aplicación). Admite 32 idiomas, español incluido, y 40.000 caracteres por petición. Va sin normalización de texto: los números y símbolos hay que escribirlos ya normalizados, algo a tener en cuenta con las frases que lleven importes.
  - TTS por HTTP: `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream`, `output_format` por defecto `mp3_44100_128` (el navegador recibe `audio/mpeg`). `optimize_streaming_latency` está obsoleto: se elige el modelo, no el parámetro.
  - Scribe v2 Realtime transcribe en más de 90 idiomas. Probado con la API: `language_code` = `es`, `spa` y sin código dan la misma transcripción. Se usa `es` (ISO 639-1, como el resto del repo).
- Medido con la API (2026-11-08, `eleven_flash_v2_5`, mp3, desde una conexión doméstica):
  - **Voz:** `ELEVENLABS_VOICE_ID=ZmOvXLYy49UISWCUznMW` (Ciro, voz profesional de la cuenta: hombre, castellano peninsular `es-ES`, "deep, cheerful and warm"). La API la lista con `eleven_flash_v2_5` entre sus modelos verificados para español `es-ES`, y funciona con él. Elegida a oído por el equipo.
  - **Latencia al primer byte** (TTS HTTP en streaming, conexión nueva cada vez). Con **Ciro**, "Te ha restado unos cuatrocientos setenta euros.", 3 llamadas tras descartar la primera: mediana **~190 ms** (190–200 ms). Con Carolina, "Te ha restado unos 470 euros.", 5 llamadas: mediana ~160 ms (150–430 ms); Lydia ~150 ms (3 llamadas). Conectar TLS suma ~40 ms aparte. Scribe: no se midió la latencia (solo que transcribe bien). La medición formal de 10 intentos sigue siendo T2-16.
  - **Arranque en frío:** la **primera** llamada con cada una de las tres voces de la biblioteca (Carolina, Lydia, Carmelo) tardó **7–11 s** hasta el primer byte; las siguientes, ~150 ms. Con Ciro, cuya primera llamada se hizo ya con la voz de la cuenta, la primera tardó ~730 ms: no se vio el arranque de segundos, pero no se puede descartar que ocurra tras un rato sin uso. Hay que hacer una llamada de calentamiento al arrancar el backend (y antes de la demo) con la voz configurada.
  - **Cifras sin normalizar:** en 3 repeticiones, "42.380 euros" se lee de forma inestable (la transcripción devolvió "42 380", "42.380" y "4380"). "0,25 puntos" y "61 %" salieron bien las 3 veces, aunque una primera prueba de "0,25 puntos" duró el doble y salió repetida. Con las cifras escritas en palabras ("cuarenta y dos mil trescientos ochenta euros", "cero coma veinticinco puntos", "sesenta y uno por ciento") las tres frases salieron estables. Ojo: Scribe devuelve cifras en dígitos aunque el audio las diga con palabras, así que esta prueba sirve para detectar lecturas erróneas pero no para distinguir cómo suena cada una.
- Decisión sobre cifras: Flash v2.5 no normaliza el texto. `voice/` debe convertir las cifras a palabras **de forma determinista antes del TTS**, **después del guardián**. El guardián valida las cifras en dígitos contra `calc_trace`; si la conversión fuera antes, no podría compararlas. Orden: Explicador → guardián (dígitos) → `voice/` (cifras a palabras, solo para el audio) → TTS. El texto en pantalla conserva los dígitos. Cubre importes en euros (con miles y decimales), porcentajes, puntos y fechas. La conversión es una función pura con tests propios.
- Motivo: fijar los IDs ahora desbloquea T0-06 y T1-21 y evita que se copien de memoria.
- Alternativas descartadas: Carolina (`UOIqAnmS11Reiei1Ytkc`, voz de la biblioteca, mujer peninsular) y Lydia (`SDVJaMLoJa7wc3s2sn7d`, mujer peninsular): elegida Ciro a oído por el equipo. Antes de eso Carolina se había preferido sobre Lydia por ritmo (~14 frente a ~19 car/s en una frase de prueba).
- Consecuencias: `.env.example` lleva ya los tres IDs. T1-21 (`voice/`) implementa la conversión de cifras a palabras y el calentamiento de la voz; T0-06 puede usar el `voice_id`. Si la voz o la latencia fallan en T2-16, se cambia de voz o de modelo, no de proveedor (decisión 4).

### D-044 · Eventos de replay (T0-10): formato del texto como entrada de fuente
- Fecha: 2026-11-08 · Autor: Manu · Estado: Propuesta
- Contexto: T0-10 redacta los tres eventos de D-020 en `data/events/replay/*.json`. Más adelante la app obtendrá los eventos scrapeando noticias y datos de mercado, y el analizador los interpretará; hoy estos JSON son mocks de esa entrada.
- Decisión:
  - `text` imita una noticia o un comunicado tal como lo recibiría la app de una fuente: resumen fiel en español de España de qué pasó, quién, cuándo y los hechos o citas clave, **sin interpretar el impacto** sobre carteras ni decir qué hacer. Solo lleva cifras que aparecen en las fuentes de `source_urls`; ninguna estimada.
  - Fuentes verificadas: BCE (comunicado oficial en español, Euronews y la encuesta de Reuters recogida por Bolsamanía e investingLive para el consenso); petróleo (copias de Reuters en The Star y Arab News, The National e Irish Times); NVIDIA (nota de prensa oficial y Yahoo Finance).
  - `occurred_at` (UTC): BCE `2025-06-05T12:15:00Z` (comunicado a las 14:15 CEST); petróleo `2025-06-13T01:42:00Z` (primera cotización documentada del salto del Brent según Reuters; los ataques empezaron hacia las 03:00 hora de Teherán, las 23:30Z del día 12, y se usa la reacción del mercado para que la fecha UTC sea el 13); NVIDIA `2025-02-26T21:20:00Z` (nota publicada a las 16:20 ET, tras el cierre).
  - `consensus` solo en el BCE (D-021): `rate_change_bp` esperado y real `-25`, con la encuesta de Reuters a 81 economistas del 29 de mayo de 2025.
  - `fallback_chain` describe la cadena causal sin ningún dígito (se convierte en `causal_chain`, que los rechaza) y sin órdenes.
  - Sin `observed` ni `observed_source`: los calcula T1-09. `illustrative: false` porque son eventos reales.
  - Fichero añadido fuera de la fila de T0-10: `backend/tests/test_replay_events.py` (valida los JSON contra `EventIn` y estas reglas).
- Motivo: si el texto ya parece una entrada de fuente, el analizador se prueba hoy en las mismas condiciones que tendrá con scraping, y no se le dan pistas de impacto que debería deducir él.
- Alternativas descartadas: redactar `text` como explicación del impacto (mezcla entrada y salida del analizador); poner la hora de los ataques en el evento del petróleo (cae el 12 de junio en UTC).
- Consecuencias: T1-09 añade `observed` sin tocar el resto. T1-15 (analizador) recibe `text` como si viniera de una fuente. Si el scraping llega a existir, debe producir `text` con este mismo estilo.

### D-045 · Históricos y `observed` (T1-09): series de factores, formato CSV y sesión de reacción
- Fecha: 2026-11-08 · Autor: Jaime · Estado: Propuesta
- Contexto: T1-09 descarga los históricos y calcula `observed` (D-025). `SPEC.md` §8.1 solo proponía las series, ningún documento fijaba el formato de los CSV ni qué sesión recoge un evento.
- Decisión:
  - `data/prices/<asset_id>.csv`: `date,close,adj_close`, 3 años, en la divisa de cotización y solo para activos `yahoo:`. `data/factors/<FACTOR>.csv`: `date,value`. Los cierres de la sesión aún abierta no se guardan.
  - Series: `EQ_GLOBAL` = `IWDA.AS` (MSCI World en EUR), `EQ_US_TECH` = `^NDX`, `OIL` = `BZ=F`, `EURUSD` = `EURUSD=X` y `RATES_EUR` = curva AAA a 10 años del BCE, como **fracción** (`0.0264` = 2,64 %), para restar directamente y obtener el shock en la unidad del contrato.
  - Sesión que recoge el evento: la del día de `occurred_at` en UTC; si es a partir de las 21:00 UTC (tras el cierre de EE. UU.), la del día siguiente. `observed` compara ese cierre con el anterior, con 5 decimales. `companies` se rellena solo en NVIDIA (`NVDA`).
  - `scripts/fetch_prices.py` no añade dependencias: usa `httpx`, ya presente en el entorno de desarrollo. Con `--observed-only` recalcula sin red.
- Motivo: Yahoo no publica la rentabilidad del Bund a 10 años. La serie Svensson del Bundesbank marca −5 pb el 5 de junio de 2025 (2,60 → 2,55) y la curva del BCE, con cierre a las 17:00 CET, +2,4 pb. Se usa la del BCE porque recoge la reacción a una decisión publicada a las 14:15 CEST.
- Alternativas descartadas: Bundesbank (ver motivo); `^TNX` (es el bono de EE. UU.); `yfinance` (dependencia nueva para una sola petición HTTP).
- Consecuencias:
  - T1-02 lee estos CSV, y el cambio EUR/USD sale de `data/factors/EURUSD.csv`. T1-12 debería usar `adj_close` para las rentabilidades.
  - Datos reales que el equipo debe conocer: el día del BCE la rentabilidad a 10 años **sube** 2,4 pb, así que `fallback_chain` de `bce-2025-06` ("bajan… la rentabilidad de los bonos", "tienden a ganar valor") no coincide con `observed`.
  - `EQ_GLOBAL` cotiza en Ámsterdam y cierra antes que Wall Street: en NVIDIA marca +0,18 % frente a −2,75 % de `^NDX`, y subestima los movimientos de la tarde en EE. UU.
  - `backend/tests/test_replay_events.py` (de T0-10) pasa a exigir `observed`. Fichero añadido fuera de la fila de T1-09: `backend/tests/test_fetch_prices.py`. `SPEC.md` §8.1 y §12 actualizados.

### D-XXX · Contratos de activo, precio y reset de demo (T1-03): `AssetOut`, `PriceOut`, `DemoResetRequest/Out`
- Fecha: 2026-11-08 19:00 · Autor: Alons · Estado: Propuesta
- Contexto: tres interfaces del diseño no tenían modelo en `app/schemas/`: la respuesta de `GET /assets/lookup` (RF-01), el `PriceOut` que devuelven `prices.latest()` y `history()` (§4.1) y el cuerpo y la respuesta de `POST /demo/reset` (§4.6). Los contratos ya estaban cerrados, así que van en un PR de contrato aparte, antes de T1-02 y T1-03.
- Decisión:
  - `AssetOut` (en `schemas/portfolio.py`): `id`, `isin`, `ticker`, `name`, `asset_type`, `asset_class`, `currency`, `ter` (fracción o `null`), `transferable` y `price_kind`, los campos de la tabla `asset` salvo `price_source`, que es interno. `GET /assets/lookup?q=` devuelve `list[AssetOut]` y busca por ISIN, ticker o nombre sin distinguir mayúsculas; `q` vacío da 422 y sin coincidencias, `[]`. Ruta en `api/assets.py`.
  - `PriceOut` (en `schemas/prices.py`, sin endpoint): `asset_id`, `price` (8 decimales, en la divisa del activo), `currency`, `price_at` (instante del dato, no de la consulta), `price_kind` y `source: SourceRef`, para que quien valore lo pase tal cual a la traza.
  - `DemoResetRequest {preload: bool = false}` (cuerpo opcional) y `DemoResetOut {portfolio_ids, preloaded_event_ids}` (en `schemas/demo.py`). `POST /demo/reset` vive en `api/demo.py` y comprueba `DEMO_MODE` (403 `DEMO_MODE_DISABLED`). `/demo/dca/run` (T1-06) y `PUT /demo/clock` (T2-03) se añaden en ese mismo fichero.
  - Las rutas nuevas responden ya sobre el mock (como en D-036): `portfolio.service.lookup_assets(q)` busca en los ejemplos `AssetOut*` y `portfolio.service.reset_demo()` devuelve los IDs. `preload` no reproduce eventos todavía y `preloaded_event_ids` sale vacío hasta que existan el pipeline (T1-15) y la integración (T2-03).
  - Ficheros fuera de la fila de T1-03: `backend/app/schemas/{prices,demo}.py`, los ejemplos nuevos, `backend/app/portfolio/mock.py`, `backend/tests/test_asset_demo_contract.py`, la lista de `test_schema_examples.py` y lo regenerado por `make gen-api`.
- Motivo: así T1-02, T1-03 y T1-19 (alta en el frontend) trabajan en paralelo contra tipos fijos.
- Alternativas descartadas: que `/demo/reset` responda 204 sin cuerpo (el frontend no sabría qué eventos quedan precargados); un `AssetLookupOut` envuelto (`GET /portfolios` ya devuelve una lista sin envolver).
- Consecuencias: T1-02 devuelve `PriceOut` en `latest()` y `history()`. T1-03 sustituye el mock de `lookup_assets` y `reset_demo` por la BD. T1-19 usa `AssetOut` para el autocompletar. T2-03 rellena `preloaded_event_ids` con el `preload`.

### D-XXX · Precios offline (T1-02): lectura de `data/prices` y `data/factors/EURUSD.csv`, catálogo desde `assets.json` y precios en memoria
- Fecha: 2026-11-08 19:30 · Autor: Alons · Estado: Propuesta
- Contexto: T1-02 lee sin red (D-014) los CSV de T1-09 (D-045). Además `prices` necesita la divisa, el tipo de precio y la fuente de cada activo, que están en la tabla `asset` de `portfolio`, y `portfolio` llama a `prices` para valorar.
- Decisión:
  - Lectura del formato de D-045: de `data/prices/<asset_id>.csv` (`date,close,adj_close`) se usa `close`, el cierre en la divisa del activo; el tipo de cambio sale de `data/factors/<PAR>.csv` (`date,value`; `EURUSD` = dólares por euro). El orden de las filas da igual; las líneas vacías se ignoran; un valor no positivo o no numérico hace fallar la carga con el fichero y la línea. Sin fichero, serie vacía.
  - `prices` lee divisa, `price_kind` y `price_source` de `data/seed/assets.json` (`prices/catalog.py`), no de la tabla `asset`: así no hay dependencia circular con `portfolio`. Los activos solo existen si están en ese catálogo (el alta usa `/assets/lookup`).
  - Modo offline: los CSV se leen una vez y se guardan en memoria (`OfflineCsvProvider`). Las tablas `price` y `fx_rate` quedan para el proveedor en directo (D-026), que no existe todavía; con cualquier `MARKET_DATA_PROVIDER` se usa el offline.
  - `latest()` devuelve el último cierre con fecha no posterior a `clock.now()` (respeta `DEMO_CLOCK`); `price_at` es la fecha del cierre a las 00:00 UTC. `fixed:<valor>` vale lo mismo todos los días, con `price_at` = hoy. Sin dato: 503 `PRICE_UNAVAILABLE`; activo fuera del catálogo: 404 `NOT_FOUND`.
  - `fx_rate(pair)` busca el par directo y, si no está, el inverso (`USDEUR` = 1 / `EURUSD`, redondeado a 8 decimales como `NUMERIC(20,8)`); misma divisa, `1`. Además de la interfaz de §4.1, `fx_quote(pair, at)` devuelve tipo, fecha y `SourceRef` (`kind: fx`) para las trazas.
  - Los tests cambian de proveedor con `tests/fakes/price_provider.py` (`FakePriceProvider` + `use_price_provider`). Ficheros fuera de la fila de T1-02: `backend/tests/fakes/__init__.py` y `backend/tests/test_prices.py`.
- Motivo: es lo mínimo que valora en < 300 ms sin red ni carga previa en BD, y lee los CSV de T1-09 tal cual.
- Alternativas descartadas: cargar los CSV en la tabla `price` desde `seed_db.py` (la tabla no guarda `price_kind` y haría falta una migración); leer la tabla `asset` desde `prices` (rompe la frontera por `service.py`).
- Consecuencias: T1-03 valora con `prices.latest` y `fx_quote("USDEUR")` (inverso de `EURUSD`). Un activo `yahoo:` sin CSV responde `PRICE_UNAVAILABLE`. Los tests usan el proveedor falso, salvo uno que comprueba los CSV reales del repo.
