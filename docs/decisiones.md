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
| [D-025](decisiones/D-025-magnitudes-de-los-datos.md) | 2026-11-08 | Las magnitudes de un evento salen de los datos | Sustituida por D-083 (solo en lo de «el LLM elige canales»; las magnitudes siguen saliendo de `observed`) |
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
| [D-062](decisiones/D-062-traspaso-fondo-fondo-t1-05.md) | 2026-11-09 | Traspaso fondo → fondo (T1-05): participaciones y coste de los lotes nuevos, libro y error con alternativa | Propuesta |
| [D-063](decisiones/D-063-tests-backend-en-paralelo.md) | 2026-11-09 | Tests del backend en paralelo con pytest-xdist (T1-23) | Propuesta |
| [D-064](decisiones/D-064-proyeccion-dca-t1-14.md) | 2026-11-09 | Proyección con DCA (T1-14): horizonte, capitalización, aportación y meta ausente | Propuesta |
| [D-065](decisiones/D-065-modo-demo-produccion-precios.md) | 2026-11-09 | Modo demo y modo producción: precios en directo y proveedor | Propuesta |
| [D-066](decisiones/D-066-explicador-t1-17.md) | 2026-11-09 | Explicador (T1-17): contexto precargado, frase a frase, plantillas y textos de otros módulos | Propuesta |
| [D-067](decisiones/D-067-alta-cartera-y-selector-t1-19.md) | 2026-11-09 | Alta de posiciones y selector de cartera en la UI (T1-19) | Propuesta |
| [D-068](decisiones/D-068-ui-operaciones-dca-t1-20.md) | 2026-11-09 | UI de operaciones y DCA (T1-20): registro sin vista previa, reparto exacto en porcentaje y `apiPatch` | Propuesta |
| [D-069](decisiones/D-069-voz-elevenlabs-t1-21.md) | 2026-11-09 | Voz con ElevenLabs (T1-21): mock sin clave, cifras a palabras en `voice/numbers.py`, calentamiento desde el router y `httpx` + `websockets` como dependencias | Propuesta |
| [D-070](decisiones/D-070-voz-frontend-t2-14.md) | 2026-11-09 | Voz en el frontend (T2-14): PCM 16 kHz con AudioWorklet, cola de audio por frase, plan B siempre visible y clientes en `src/api/` | Propuesta |
| [D-071](decisiones/D-071-latencia-voz-t2-16.md) | 2026-11-09 | Latencia de voz (T2-16): 9/10 por debajo de 2 s con una primera frase corta en el prompt del explicador; sin cambiar de modelo ni de voz | Propuesta |
| [D-072](decisiones/D-072-pregunta-formato-chat.md) | 2026-11-09 | Pregunta en formato chat: historial, barra fija abajo, «Leer en voz alta» para todas las respuestas y texto línea a línea | Propuesta |
| [D-073](decisiones/D-073-status-precalculado-t2-04.md) | 2026-11-09 | Estado del widget (T2-04): precalculado en memoria, lectura sin modelo y refresco cada 10 s | Propuesta |
| [D-074](decisiones/D-074-openapi-typescript-devdependency.md) | 2026-11-09 | `openapi-typescript` como devDependency del frontend con versión exacta; `make gen-api` sin red | Propuesta |
| [D-075](decisiones/D-075-ajuste-demo-t2-02.md) | 2026-11-09 | Ajuste de demo (T2-02): se sustituye por evento, entra en el cambio semanal e ignora activos vendidos | Propuesta |
| [D-076](decisiones/D-076-avisos-t2-08.md) | 2026-11-09 | Avisos de evento (T2-08): un aviso por evento y cartera, umbral gemelo del widget y sin migración | Propuesta |
| [D-077](decisiones/D-077-explain-move-t2-07.md) | 2026-11-09 | «¿Por qué ha bajado?» (T2-07): ventana, flujos y ajustes de demo del periodo | Propuesta |
| [D-078](decisiones/D-078-radar-t2-05.md) | 2026-11-09 | Radar (T2-05): reglas, divisa desconocida y traspaso sin tributar ligado al plan | Propuesta |
| [D-079](decisiones/D-079-asistente-flotante-y-aviso-ia-sin-audio.md) | 2026-11-09 | Asistente flotante en vez de pestaña «Pregunta», modo conversación por voz y aviso de IA sin audio | Propuesta |
| [D-080](decisiones/D-080-datos-demo-t2-15.md) | 2026-11-09 | Datos de la demo (T2-15): reloj, última aportación de Laura y formato de la agenda | Propuesta |
| [D-081](decisiones/D-081-traza-en-la-ui-t2-11.md) | 2026-11-10 | «¿De dónde sale?» en la UI (T2-11) | Propuesta |
| [D-082](decisiones/D-082-integracion-t2-03.md) | 2026-11-10 | Integración (T2-03): mocks que se quedan, patrones del guardián en el analizador y `GUARDIAN_LLM_CHECK` fuera | Propuesta |
| [D-083](decisiones/D-083-cifras-todos-factores-observados.md) | 2026-11-10 | Las cifras usan todos los factores observados; el analizador solo redacta (T2-26) | Propuesta |
| [D-084](decisiones/D-084-umbral-exposicion-agenda.md) | 2026-11-10 | Exposición de la agenda: umbral de beta por factor y beta significativa (T2-06) | Propuesta |
| [D-085](decisiones/D-085-recharts-grafica-cartera.md) | 2026-11-10 | Recharts para la gráfica de evolución de la cartera (T2-18) | Propuesta |
| [D-086](decisiones/D-086-aviso-movimiento-mercado-t2-21.md) | 2026-11-10 | Aviso por movimiento de mercado (T2-21): parte sin explicar, comprobación al leer y apagado en demo | Propuesta |
| [D-087](decisiones/D-087-bandeja-avisos-leidos-en-navegador.md) | 2026-11-10 | Bandeja de avisos (T2-20): «leído» se guarda en el navegador, sin ruta nueva | Propuesta |
| [D-088](decisiones/D-088-evaluacion-30-preguntas.md) | 2026-11-10 | Evaluación de respuestas (T3-01): 10 de impacto, 10 generales, 10 trampa y un detector de órdenes propio | Propuesta |
| [D-089](decisiones/D-089-shocks-en-produccion.md) | 2026-11-10 | De dónde sale el shock de un evento en producción: cierre observado y rango histórico | Propuesta |
| [D-090](decisiones/D-090-explicador-sin-repeticiones-ni-relleno.md) | 2026-11-10 | Explicador (T3-10): las repeticiones y el relleno tras un reintento se callan sin contar como bloqueo; evaluación de 40 preguntas | Propuesta |
| [D-091](decisiones/D-091-e2e-guion-playwright.md) | 2026-11-10 | E2E del guion con `@playwright/test` contra el stack real en modo offline (T3-02) | Propuesta |
| [D-092](decisiones/D-092-gestion-carteras-t4-10.md) | 2026-11-10 | Gestión de carteras: Laura y Javier siguen por defecto mientras Q10 esté abierta, y SQLite con claves foráneas (T4-10) | Propuesta |
| [D-093](decisiones/D-093-factores-en-directo-t4-01.md) | 2026-11-10 | Cierres de los 5 factores en directo: Yahoo y BCE, tabla `factor_close` y fuente aparte del `PriceProvider` (T4-01) | Propuesta |
| [D-094](decisiones/D-094-calibracion-umbrales-t3-04.md) | 2026-11-10 | Calibración de umbrales con datos reales (T3-04): se mantienen los de estado, avisos y confianza | Propuesta |
| [D-095](decisiones/D-095-fases-rediseno-y-entrega.md) | 2026-11-10 | Fase 5 de rediseño visual y fase 6 de entrega; la fase 3 queda para el endurecimiento y la fase 4 se valida | Aceptada (acuerdo del equipo) |
| [D-096](decisiones/D-096-shock-medido-automatico-t4-04.md) | 2026-11-10 | Shock medido automático: lógica de `fetch_prices.py` en `events`, eventos pendientes de cierre y cifras desde el día siguiente (T4-04) | Propuesta |
| [D-097](decisiones/D-097-limite-avisos-por-cartera.md) | 2026-11-10 | El límite de 2 avisos por semana es por cartera; la bandeja junta todas | Aceptada |
| [D-098](decisiones/D-098-ingesta-noticias-bce-t4-05.md) | 2026-11-10 | Ingesta de noticias: solo las decisiones de política monetaria del BCE; resultados y OPEP, sin fuente usable todavía (T4-05) | Propuesta |
| [D-099](decisiones/D-099-betas-recalculadas-solas-t4-03.md) | 2026-11-10 | Betas recalculadas solas: función de `impact` sobre las series de `prices`, cada semana y al dar de alta un activo (T4-03) | Propuesta |
| [D-100](decisiones/D-100-cartera-elegida-url-y-navegador-t4-13.md) | 2026-11-10 | Cartera elegida: `?p=` manda y el navegador la recuerda (T4-13) | Propuesta |
| [D-101](decisiones/D-101-catalogo-fijo-ampliado-t4-26.md) | 2026-11-10 | Catálogo fijo ampliado y comprobado en Yahoo en lugar de catálogo abierto en el MVP (T4-26) | Propuesta |
| [D-102](decisiones/D-102-fuentes-de-noticias-t4-28.md) | 2026-11-10 | Fuentes de noticias: Google Noticias (RSS de búsqueda), RSS de Yahoo Finance y de la Fed; GDELT opcional (T4-28) | Propuesta |
| [D-103](decisiones/D-103-impacto-de-una-noticia-t4-29-t4-30.md) | 2026-11-10 | Impacto de una noticia: Claude elige canales y dirección; el motor pone el tamaño con datos (medido o estimado por días de noticia fuerte) (T4-29, T4-30) | Propuesta |
| [D-104](decisiones/D-104-laboratorio-de-componentes-t5-01.md) | 2026-11-10 | Laboratorio de componentes (`/lab`) y dependencias de la fase 5 (T5-01) | Aceptada (acuerdo del equipo, 10-nov) |
| [D-105](decisiones/D-105-rojo-de-marca-t5-10.md) | 2026-11-11 | Rojo de marca y jerarquía de color (T5-10) | Aceptada (dirección de rebranding solicitada por Javi) |
| [D-106](decisiones/D-106-avisos-por-noticia-t4-31.md) | 2026-11-11 | Avisos por noticia: umbral según el perfil, un aviso nuevo al día y en la demo solo con `make news-alerts` (T4-31) | Propuesta |
| [D-107](decisiones/D-107-asistente-sobre-cualquier-cartera-t4-14.md) | 2026-11-11 | El asistente ve todos los datos de cada cartera y el guardián comprueba las cifras por cartera (T4-14) | Propuesta |
| [D-108](decisiones/D-108-noticias-cada-5-minutos-tb-01.md) | 2026-11-11 | Noticias en producción cada 5 minutos: frecuencia por fuente, espera al ser limitados y avisos tras cada pasada (TB-01, TB-02) | Propuesta |
<!-- INDICE:FIN -->
