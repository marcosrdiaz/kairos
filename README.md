# KAIROS

KAIROS traduce eventos financieros (una decisión del BCE, un salto del petróleo, unos resultados, un movimiento de divisas) a lo que significan **en euros para tu cartera**, con un rango, un nivel de confianza y la traza de cada cifra.

- **Las cifras no las inventa la IA.** Todo número sale del gestor de cartera o del motor de impacto, que son deterministas. Claude solo redacta a partir de esos resultados.
- **Contexto, no órdenes.** KAIROS no dice «compra» ni «vende». Cada texto pasa por un guardián que bloquea las recomendaciones.
- **Toda cifra es trazable.** Cada número de la app lleva un enlace «¿De dónde sale?» con sus entradas, su fórmula y sus fuentes.

> Proyecto del hackathon Hack Finance (BEST UC3M, noviembre de 2026). **No es asesoramiento financiero.** Las carteras de ejemplo (Laura y Javier) son ilustrativas.

## Requisitos

- **Docker** con Docker Compose v2 (Docker Desktop en Windows y macOS). Es lo único necesario para ejecutar la app.
- Libres los puertos **5173** (app), **8000** (API) y **5432** (PostgreSQL).
- Opcional: claves de Anthropic y ElevenLabs (ver [Claves opcionales](#claves-opcionales)). Sin ellas la app funciona entera.

## Puesta en marcha

Desde la carpeta del proyecto:

```bash
# 1. Configuración: copia el ejemplo (no hace falta tocarlo para la demo)
cp .env.example .env            # PowerShell: Copy-Item .env.example .env

# 2. Construye y arranca base de datos, carga de datos, backend y frontend
docker compose up --build       # equivale a `make up`
```

La primera vez tarda unos minutos en construir las imágenes. Está listo cuando el servicio `seed` termina (carga las carteras y calcula las betas; acaba con `factor_beta: 75 filas`) y el backend responde.

| Qué | Dirección |
| --- | --- |
| **App** | http://localhost:5173 |
| Panel de contexto | http://localhost:5173/panel |
| Pantalla de inicio del móvil con el widget | http://localhost:5173/widget |
| API (documentación interactiva) | http://localhost:8000/docs |
| Estado del backend | http://localhost:8000/api/v1/health |

Para pararlo: `Ctrl+C` o `docker compose down`. Para empezar de cero, borrando la base de datos: `docker compose down -v`.

### El fichero `.env`

`.env.example` deja la app en **modo demo**, que es lo que espera el guion:

| Variable | Valor de la demo | Para qué |
| --- | --- | --- |
| `DEMO_MODE` | `true` | Activa los controles de demo (`/demo/reset`, `/demo/replay`, `/demo/clock`) |
| `DEMO_CLOCK` | `2026-11-06T18:00:00Z` | Fija el reloj al último cierre de `data/prices`, para que las cifras salgan siempre iguales. Vacío = reloj real |
| `MARKET_DATA_PROVIDER` | `offline` | Precios de `data/prices` (CSV con históricos reales). No necesita red. Con `yahoo` (y `DEMO_MODE=false`), precios en directo: modo producción (D-065) |
| `NEWS_POLL_MINUTES` | `5` | Solo con `DEMO_MODE=false`: el servicio `news-updater` busca noticias, las clasifica y lanza sus avisos cada 5 min (Google Noticias, cada `NEWS_GOOGLE_MINUTES`). En la demo no busca |

Sin `.env` la app también arranca, pero con el reloj real, así que las cifras del guion no coinciden con las del día de los datos.

### Claves opcionales

| Variable | Con la clave | Sin la clave |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Claude analiza los eventos y redacta las respuestas. Las cifras siguen saliendo del motor | Plantillas con los mismos datos del motor y cadenas causales escritas a mano |
| `ELEVENLABS_API_KEY` | Preguntas por voz (Scribe) y respuestas habladas (Flash v2.5) | Solo texto. El asistente funciona igual por escrito |

Tras cambiar `.env`, vuelve a ejecutar `docker compose up --build`.

## Probar el guion de demo (3 minutos)

La app abre con la cartera de **Laura**. Para ver la de **Javier**, añade `?p=javier` a la dirección (p. ej. http://localhost:5173/inicio?p=javier) o usa el selector de cartera.

Antes de empezar, deja la demo en su estado inicial: en **Cartera**, «Cargar carteras de ejemplo». También se puede hacer por API:

```bash
curl -X POST http://localhost:8000/api/v1/demo/reset -H "Content-Type: application/json" -d '{"preload": true}'
```

`preload` reproduce el BCE y el petróleo como eventos de hace 4 días, así que el panel ya tiene contexto y el widget arranca en «Tranquilo».

| Paso | Qué hacer | Qué se ve |
| --- | --- | --- |
| 1 | Abrir **Inicio** y **/widget** | Distribución de la cartera y widget en **Tranquilo** |
| 2 | **Cartera** → radiografía | Exposición real por look-through: país, divisa y empresas que se repiten entre fondos |
| 3 | Lanzar el evento en directo (comando de abajo) | El widget pasa a **Atento** y llega el aviso con el impacto en euros (rango y confianza) |
| 4 | Asistente (botón abajo a la derecha): «¿Por qué ha bajado?» | Respuesta con la cadena causal y cifras del motor |
| 5 | Abrir **/panel** | Los eventos traducidos a la cartera, riesgos y oportunidades según el plan, y la agenda |
| 6 | Cambiar a Javier (`?p=javier`) | La misma noticia con otro impacto y otro mensaje |
| 7 | Asistente: «¿Voy bien?» | Proyección con el DCA frente al objetivo |
| 8 | Pulsar cualquier cifra («¿De dónde sale?») | Traza con entradas, fórmula, fuentes y cálculos padre |

Evento del paso 3 (resultados de NVIDIA, febrero de 2025):

```bash
make replay EVENT=nvda-2025-02
# sin make:
curl -X POST http://localhost:8000/api/v1/demo/replay/nvda-2025-02
```

Los otros eventos del replay son `bce-2025-06` y `oil-2025-06`. Están en `data/events/replay/`.

> En PowerShell, usa `curl.exe` en vez de `curl`. En el comando del reset, el JSON va así: `-d '{\"preload\": true}'`.

### Comprobación automática del guion

Un script recorre los 8 pasos contra el backend en marcha y para en el primero que falle. **Resetea la demo.**

```bash
docker compose exec backend python /scripts/demo_smoke.py
```

Salida esperada: ocho líneas `OK` y `Guion completo.`. En Git Bash para Windows, antepón `MSYS_NO_PATHCONV=1` al comando.

## Desarrollo

Además de Docker, hacen falta [uv](https://docs.astral.sh/uv/) (Python 3.12), Node.js 22 y `make`.

```bash
bash scripts/setup-dev.sh   # una vez tras clonar: dependencias del frontend y playwright-cli
make test                   # pytest (backend) + vitest (frontend)
make lint                   # ruff + mypy, eslint + tsc
make seed                   # migraciones + carteras de Laura y Javier + betas
make betas                  # recalcula las betas desde data/prices
make gen-api                # regenera los tipos TS y los mocks desde el backend
```

Las normas del equipo (tareas, ramas, contratos, decisiones) están en [`CLAUDE.md`](CLAUDE.md) y [`docs/TABLERO.md`](docs/TABLERO.md).

### Estructura

```
backend/    FastAPI + SQLAlchemy. Un módulo por dominio (portfolio, prices, exposure, impact,
            events, agents, alerts, status, planning, voice); se llaman entre sí por su service.py
frontend/   React + Vite + TypeScript. Llamadas al backend solo desde src/api/
data/       Semilla (carteras, activos, composiciones), precios y factores históricos, eventos
scripts/    Carga de datos, betas, replay, smoke del guion, generación de tipos
docs/       Producto, diseño del MVP, especificación técnica, decisiones y tablero
```

## Limitaciones conocidas

- **No hay login ni usuarios.** Cualquiera que abra la app puede ver y modificar cualquier cartera (Laura, Javier o las que se den de alta), y también registrar operaciones y planes de aportación. Es una decisión del MVP (D-013): las carteras son ilustrativas, la app corre en local y no mueve dinero real. Trabajo futuro: cuentas con autenticación, y que cada ruta del backend compruebe que la cartera es de quien la pide.
- **Las noticias vienen del modo replay.** Son 3 eventos reales (BCE, petróleo y NVIDIA) con los movimientos de mercado observados ese día. No hay lectura de noticias en directo.
- **Precios offline.** En la demo, los precios y los tipos de cambio salen de `data/prices`, con históricos reales hasta el 6 de noviembre de 2026.
- **Las composiciones de los fondos** son las principales posiciones publicadas (con fecha y fuente) más un «Otros».
- **Los impactos son estimaciones.** Salen de betas históricas por factor, por eso se dan como rango con un nivel de confianza.

## Problemas frecuentes

| Síntoma | Solución |
| --- | --- |
| `port is already allocated` | Libera los puertos 5173, 8000 o 5432 (p. ej. otro PostgreSQL local) y repite |
| Los impactos salen con el rango cerrado (`low` = `high`) | Faltan las betas: `make betas` o `docker compose run --rm seed` |
| Las cifras no coinciden con el guion | Comprueba que existe `.env` con `DEMO_CLOCK` y resetea la demo |
| Quiero volver al estado de fábrica | `docker compose down -v` y `docker compose up --build` |

## Documentación

| Documento | Contenido |
| --- | --- |
| [`docs/kairos-spec.md`](docs/kairos-spec.md) | Producto: problema, usuarios, funcionalidades y guion |
| [`docs/superpowers/specs/2026-11-08-kairos-mvp-design.md`](docs/superpowers/specs/2026-11-08-kairos-mvp-design.md) | Diseño técnico del MVP y contratos |
| [`docs/SPEC.md`](docs/SPEC.md) | Stack, modelo de datos, API, algoritmos y agentes |
| [`docs/INGENIERIA.md`](docs/INGENIERIA.md) | Requisitos, casos de uso y plan de pruebas |
| [`docs/decisiones.md`](docs/decisiones.md) | Registro de decisiones |
