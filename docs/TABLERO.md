# Tablero del equipo — KAIROS

Documento vivo: quién hace qué, en qué estado está y qué bloquea a quién. Lo leen y escriben las personas y sus sesiones de Claude Code.

**Plazo:** domingo 8 de noviembre (tarde) → **miércoles 11 de noviembre a las 23:59** (cierre del formulario de BEST UC3M).

**Reglas para no pisarse**
- Cada persona edita **solo su sección** (§4) y añade filas al final de las tablas compartidas (§5, §6, §7).
- Estados de tarea: `⬜ pendiente` · `🔄 en curso` · `🧪 en PR` · `✅ hecho` · `⛔ bloqueado`.
- Una tarea está hecha cuando su criterio se cumple, está en `main` y `make test` pasa.
- Actualiza tu sección al cerrar cada sesión (`/cierre`) y antes de cada checkpoint.

---

## 1. Equipo y propiedad del código

| ID | Persona | Rol | Carpetas que posee | Features |
| --- | --- | --- | --- | --- |
| P1 | _por decidir_ | Cartera y precios (backend core) | `backend/app/{portfolio,prices,core}`, `api/portfolio*.py`, `alembic/`, `docker-compose.yml`, `Makefile` | F1, F2, F4, F5, F11 (datos), trazas |
| P2 | _por decidir_ | Exposición y motor de impacto | `backend/app/{exposure,impact,status}`, `scripts/compute_betas.py` | F3, F8, F13, F24, F25, estado del widget |
| P3 | _por decidir_ | Agentes IA y eventos | `backend/app/{agents,events,alerts}`, `scripts/replay_event.py`, `scripts/eval_answers.py` | F9, F10, F12, explicador |
| P4 | **Javi** | Frontend | `frontend/` (salvo `src/voice/`) | F6, F23, UI de F1/F4/F5/F7/F24 |
| P5 | _por decidir_ | Voz, datos y entregables | `backend/app/voice`, `frontend/src/voice`, `data/`, `scripts/fetch_prices.py`, `README.md`, PDF, PowerPoint | F7 (voz), dataset, entregables |

Pendientes de asignar a P1, P2, P3 y P5: Manu, Jaime, Marcos, Alons.

Compartido: `backend/app/schemas/` (contratos, cambios por PR revisado por el consumidor), `docs/`.

**Coordinador de integración** (decide en conflictos de alcance y hace el merge final): _por decidir_. Lo natural es P1, que tiene el esqueleto y el Compose.

## 2. Checkpoints

Propuesta; ajustad a vuestros horarios de lunes a miércoles.

| Cuándo | Duración | Qué |
| --- | --- | --- |
| Cada mañana (antes de las 10:00) | Asíncrono | Cada uno actualiza *En curso* en su sección |
| Cada día, 21:30 | 15 min (llamada) | Demo desde `main`, bloqueos, validar decisiones `Propuesta`, actualizar §3 |
| Domingo 8, al acabar el reparto | 20 min | Kick-off: roles, contratos, quién hace el esqueleto |

## 3. Hitos

| Cuándo | Hito | Estado |
| --- | --- | --- |
| **Dom 8 · noche** | Roles asignados; esqueleto del repo en `main` (Compose, Makefile, carpetas, CI); **contratos + mocks publicados antes de las 23:59**; datos de ejemplo empezados | ⬜ |
| **Lun 9** | Alta de cartera y valoración; look-through de ~10 fondos/ETF; eventos replay en JSON; analizador y guardián empezados; app con 3 pestañas y widget sobre mocks | ⬜ |
| **Mar 10** | Compra/venta/traspaso/DCA; impacto en € con rango; explicador + guardián; voz de punta a punta; panel; **23:00 el guion de demo funciona entero**; decisión sobre "Si da tiempo" | ⬜ |
| **Mié 11** | **16:00 congelación** (solo fixes); README, PDF, PowerPoint, vídeo de respaldo; 3 ensayos; ZIP desde GitHub; **entrega antes de las 21:00** (3 h de margen sobre el cierre) | ⬜ |

**Regla de alcance:** lo marcado como "Si da tiempo" solo entra si el martes a las 23:00 el guion funciona entero.

## 4. Tareas por persona

> Formato de ID: `T-P<n>-<nn>`. Añade tareas al final de tu lista; no renumeres.

### P1 · Cartera y precios — _por decidir_

| ID | Tarea | Criterio de hecho | Cuándo | Estado |
| --- | --- | --- | --- | --- |
| T-P1-01 | Esqueleto: Compose (db, backend, frontend, seed), Makefile, `config.py`, `core/clock.py`, `core/trace.py`, CI (lint + test) | `make up` y `make test` funcionan en limpio | Dom | ⬜ |
| T-P1-02 | Modelos y migración: portfolio, plan, asset, price, fx_rate, transaction, tax_lot, dca_*, calc_trace | `alembic upgrade head` ok | Dom-Lun | ⬜ |
| T-P1-03 | Schemas `PortfolioOut`, `PositionOut` + `portfolio/mock.py` | Publicado antes de Dom 23:59 | Dom | ⬜ |
| T-P1-04 | Alta de posiciones + carga de cartera de ejemplo + `/demo/reset` | RF-01, RF-02 | Lun | ⬜ |
| T-P1-05 | `prices`: proveedor offline (CSV) + FX + `latest()`; interfaz para proveedor real | RF-03 | Lun | ⬜ |
| T-P1-06 | Compra/venta FIFO con casos dorados | RF-04, RF-05 | Lun | ⬜ |
| T-P1-07 | Traspaso fondo → fondo | RF-06 | Mar | ⬜ |
| T-P1-08 | DCA: planes, ejecución pendiente, confirmar/saltar, `/demo/dca/run` | RF-07 | Mar | ⬜ |
| T-P1-09 | `/traces/{calc_id}` | RF-19 | Mar | ⬜ |
| T-P1-10 | Plan del usuario (`/plan`) | RF-22 (datos) | Mar | ⬜ |

**En curso:** —
**Notas para retomar:** —

### P2 · Exposición e impacto — _por decidir_

| ID | Tarea | Criterio de hecho | Cuándo | Estado |
| --- | --- | --- | --- | --- |
| T-P2-01 | Schemas `ExposureOut`, `EventImpactOut`, `StatusOut` + mocks | Publicado antes de Dom 23:59 | Dom | ⬜ |
| T-P2-02 | Casos dorados Laura/Javier en hoja (exposición e impacto de los 3 eventos) | `tests/golden/*.json` revisado por otra persona | Lun | ⬜ |
| T-P2-03 | Look-through y solapamientos | RF-08, RF-09 | Lun | ⬜ |
| T-P2-04 | `compute_betas.py` + tabla `factor_beta` | Betas con R² y error estándar para todos los activos | Lun | ⬜ |
| T-P2-05 | Motor de impacto (mercado, divisa, resultados, rango, confianza, polaridad) | RF-10 + dorados | Mar | ⬜ |
| T-P2-06 | Estado del widget con frase precalculada | RF-13 | Mar | ⬜ |
| T-P2-07 | Radar de riesgos y oportunidades | RF-18 | Mar | ⬜ |
| T-P2-08 | Proyección con DCA ("¿voy bien?") | RF-22 | Mar | ⬜ |
| T-P2-09 | Escenarios ¿Y si…? | RF-21 (S) | Mar, si da tiempo | ⬜ |

**En curso:** —
**Notas para retomar:** —

### P3 · Agentes y eventos — _por decidir_

| ID | Tarea | Criterio de hecho | Cuándo | Estado |
| --- | --- | --- | --- | --- |
| T-P3-01 | Schemas `EventAnalysis`, `AskRequest`, SSE de `/ask` + mocks | Publicado antes de Dom 23:59 | Dom | ⬜ |
| T-P3-02 | Elegir con P5 los 3-4 eventos reales y redactar sus JSON | `data/events/replay/` completo | Dom-Lun | ⬜ |
| T-P3-03 | Analizador (modelo profundo, salida estructurada) + `/demo/replay` | RF-11, RF-12 | Lun | ⬜ |
| T-P3-04 | Guardián (patrones, cifras, reintento, plantilla) con tests | RF-16 | Lun | ⬜ |
| T-P3-05 | Explicador con contexto precargado + herramientas + `/ask` SSE | RF-15 | Mar | ⬜ |
| T-P3-06 | Avisos con umbral y límite semanal | RF-23 | Mar | ⬜ |
| T-P3-07 | Evaluación de 30 preguntas (incl. trampas "¿vendo?") | 0 órdenes de compraventa | Mar | ⬜ |

**En curso:** —
**Notas para retomar:** —

### P4 · Frontend — Javi

| ID | Tarea | Criterio de hecho | Cuándo | Estado |
| --- | --- | --- | --- | --- |
| T-P4-01 | Vite + TS + Tailwind + TanStack Query + `make gen-api`; layout móvil con 3 pestañas (Inicio · Cartera · Pregunta); mocks de API | Navega sobre mocks | Dom | ⬜ |
| T-P4-02 | Pantalla de inicio simulada con widget (3 estados, color + palabra) | RF-13 visual | Lun | ⬜ |
| T-P4-03 | Alta de cartera y selector Laura/Javier | RF-01, RF-02 | Lun | ⬜ |
| T-P4-04 | Operaciones (compra, venta, traspaso con error explicado) y DCA | RF-04–07 | Lun-Mar | ⬜ |
| T-P4-05 | Panel: resumen, eventos con cadena causal, exposición, radar, agenda | RF-17, RF-18 | Mar | ⬜ |
| T-P4-06 | "¿De dónde sale?" → traza | RF-19 | Mar | ⬜ |
| T-P4-07 | Avisos IA y "no es asesoramiento"; accesibilidad (Lighthouse ≥ 90) | RF-20, RNF-11 | Mar | ⬜ |
| T-P4-08 | Playwright del guion de demo | E2E en verde | Mar noche-Mié | ⬜ |

**En curso:** —
**Notas para retomar:** —

### P5 · Voz, datos y entregables — _por decidir_

| ID | Tarea | Criterio de hecho | Cuándo | Estado |
| --- | --- | --- | --- | --- |
| T-P5-01 | Catálogo de activos y carteras Laura/Javier (`data/seed/`) | Cuadra con la tabla "misma noticia, dos carteras" o se actualiza el pitch | Dom | ⬜ |
| T-P5-02 | Composición de ~10 fondos/ETF (gestoras / CNMV) | CSV con `as_of` y fuente | Dom-Lun | ⬜ |
| T-P5-03 | Históricos diarios 2-3 años de activos y factores | `data/prices/`, `data/factors/` | Lun | ⬜ |
| T-P5-04 | Verificar IDs de modelos ElevenLabs y voz en español; medir latencia | Anotado en `decisiones.md` | Dom | ⬜ |
| T-P5-05 | `voice/` backend (WS STT, TTS en streaming) | Audio de ida y vuelta | Lun | ⬜ |
| T-P5-06 | `src/voice/` frontend (push-to-talk, reproducción, texto) | RF-14 con explicador real | Mar | ⬜ |
| T-P5-07 | README (instalación, `.env`, ejecución, prueba) | Otro miembro lo ejecuta sin ayuda | Mar-Mié | ⬜ |
| T-P5-08 | PDF de una cara + PowerPoint + diapositiva de arquitectura | Revisado por el equipo | Mié | ⬜ |
| T-P5-09 | Vídeo de respaldo + entrega (ZIP desde GitHub + formulario BEST UC3M) | Enviado antes de Mié 21:00 | Mié | ⬜ |

**En curso:** —
**Notas para retomar:** —

## 5. Bloqueos

| Fecha/hora | Quién está bloqueado | Por qué | Necesita de | Estado |
| --- | --- | --- | --- | --- |
| | | | | |

## 6. Peticiones de contrato

Cambios en `backend/app/schemas/` o en endpoints que afectan a otra persona.

| Fecha/hora | Pide | Esquema / endpoint | Cambio | Afecta a | Estado |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## 7. Preguntas abiertas

| # | Pregunta | Quién decide | Estado |
| --- | --- | --- | --- |
| Q1 | Asignación de P1, P2, P3 y P5 entre Manu, Jaime, Marcos y Alons | Equipo | Abierta |
| Q2 | Fechas del hackathon | Equipo | Cerrada: Dom 8 tarde → Mié 11 23:59 |
| Q3 | Laura tiene RV 76% con objetivo 70% y umbral 5 pp → su widget arranca en "Revisa tu plan", pero el paso 1 del guion lo quiere "Tranquilo". ¿Subimos el umbral, cambiamos su objetivo o el guion? | P2 + P5 | Abierta |
| Q4 | "¿Voy bien?" (paso 7) depende de F11, marcada "Si da tiempo". ¿Sube a MVP o se cambia el paso? | Equipo | Abierta |
| Q5 | Qué 3-4 eventos reales usar en el replay | P3 + P5 | Abierta |
| Q6 | Fuente de consenso para medir la sorpresa de datos macro (o se omite la sorpresa en el MVP) | P3 | Abierta |
| Q7 | Modelo de negocio del pitch: B2B2C principal (propuesto en el doc de idea) | Equipo | Abierta |
| Q8 | Disponibilidad de cada uno de lunes a miércoles (trabajo, clases) para ajustar checkpoints y reparto | Equipo | Abierta |

## 8. Registro de checkpoints

| Fecha/hora | Resumen (3 líneas) | Decisiones validadas |
| --- | --- | --- |
| | | |
