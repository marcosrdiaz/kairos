# Registro de decisiones — KAIROS

Sirve para retomar el trabajo tras un `/clear` o al cambiar de persona sin repetir discusiones.

## Cómo se usa

- **Solo se añade al final.** No se borra ni se reescribe una entrada; si cambia, se crea una nueva que la sustituye y en la antigua solo se cambia *Estado* a `Sustituida por D-xxx`.
- **IDs por rango para no pisarse**: `D-0xx` equipo/general · `D-1xx` P1 · `D-2xx` P2 · `D-3xx` P3 · `D-4xx` P4 · `D-5xx` P5.
- **Estados**: `Propuesta` (falta validar con el equipo en el siguiente checkpoint) · `Aceptada` · `Sustituida por D-xxx` · `Descartada`.
- Una decisión merece entrada si: cambia un contrato o el modelo de datos, añade una dependencia, afecta a otro módulo, o la vas a olvidar en 2 horas.
- Plantilla (o usa `/decision`):

```
### D-xxx · Título corto
- Fecha: AAAA-MM-DD HH:MM · Autor: Pn · Estado: Propuesta
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
| D-004 | 2026-11-08 | Widget simulado en web móvil, sin nativo | Propuesta |
| D-005 | 2026-11-08 | Operaciones como registros, no órdenes | Aceptada |
| D-006 | 2026-11-08 | Monorepo con carpetas por dueño y `service.py` como frontera | Propuesta |
| D-007 | 2026-11-08 | Posiciones derivadas de lotes fiscales | Propuesta |
| D-008 | 2026-11-08 | `Decimal` para dinero y participaciones | Propuesta |
| D-009 | 2026-11-08 | Reloj inyectable y replay con fecha de hoy | Propuesta |
| D-010 | 2026-11-08 | Guardián determinista, validación frase a frase | Propuesta |
| D-011 | 2026-11-08 | Contexto precargado para la voz | Propuesta |
| D-012 | 2026-11-08 | Modelos y proveedores configurables por `.env` | Propuesta |
| D-013 | 2026-11-08 | Sin login: selector de cartera Laura / Javier | Propuesta |
| D-014 | 2026-11-08 | Modo de datos `offline` por defecto | Propuesta |
| D-015 | 2026-11-08 | Contratos y mocks antes del domingo 8 a las 23:59 | Propuesta |

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
- Fecha: 2026-11-08 · Autor: equipo · Estado: Propuesta
- Contexto: pregunta abierta del documento de idea; nadie confirmado en Kotlin/Swift.
- Decisión: pantalla de inicio de móvil simulada en la web con el widget como componente React.
- Motivo: el tiempo va a voz, motor e impacto, que es lo que puntúa.
- Consecuencias: F18 queda en "Después".

### D-005 · Operaciones como registros, no órdenes
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Decisión: comprar, vender, traspasar y DCA solo registran en KAIROS; el usuario ejecuta en su bróker.
- Motivo: sin licencia de intermediario; principio "contexto, no órdenes".

### D-006 · Monorepo con carpetas por dueño y `service.py` como frontera
- Fecha: 2026-11-08 · Autor: equipo · Estado: Propuesta
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
- Fecha: 2026-11-08 · Autor: equipo · Estado: Propuesta
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
- Fecha: 2026-11-08 · Autor: equipo · Estado: Propuesta
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
