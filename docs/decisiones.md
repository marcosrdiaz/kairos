# Registro de decisiones — KAIROS

Sirve para retomar el trabajo tras un `/clear` o al cambiar de tarea sin repetir discusiones.

## Cómo se usa

- **Solo se añade al final.** No se borra ni se reescribe una entrada; si cambia, se crea una nueva que la sustituye y en la antigua solo se cambia *Estado* a `Sustituida por D-xxx`.
- **IDs correlativos `D-0xx`.** Antes de añadir, haz `git pull` para no repetir ID. Añade siempre al final y actualiza el índice. `docs/decisiones.md` es una excepción a la propiedad por tarea: cualquiera puede añadir.
- **Estados**: `Propuesta` (falta validar con el equipo en el siguiente checkpoint) · `Aceptada` · `Sustituida por D-xxx` · `Descartada`.
- Una decisión merece entrada si: cambia un contrato o el modelo de datos, añade una dependencia, afecta a otro módulo, o la vas a olvidar en 2 horas.
- Plantilla (o usa `/decision`):

```
### D-xxx · Título corto
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
  - No hay coordinador de integración. El merge a `main` lo hace quien abre el PR, tras la aprobación de un revisor y con el CI en verde. Qué "Si da tiempo" entra lo decide el equipo en el checkpoint del martes a las 18:00 y se apunta aquí.
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
