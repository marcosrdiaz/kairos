# CLAUDE.md — KAIROS

KAIROS traduce eventos financieros (BCE, petróleo, resultados, divisas) al impacto en euros sobre la cartera de un inversor particular. Hackathon Hack Finance (BEST UC3M), 4 días, 5 personas trabajando en paralelo, cada una con su propia sesión de Claude Code.

Este fichero se carga en todas las sesiones. Es corto a propósito: el detalle está en `docs/`.

## Al empezar una sesión (o tras `/clear`)

1. Pregunta al humano **cómo se llama** (Manu, Jaime, Marcos, Alons o Javi) y si va a **continuar una tarea suya en curso** o a **coger una nueva**.
2. Si continúa una tarea: lee su fila y su subsección en *Notas para retomar* de `docs/TABLERO.md`.
3. Si coge una nueva: lista las tareas **disponibles de la fase actual** (la primera fase no cerrada): estado `⬜`, sin nadie en *Cogida por*, con todas sus dependencias hechas y sin ficheros en común con una tarea en curso. Que elija una y cógela con `/coger <ID>` antes de empezar.
4. Lee la tabla de *Bloqueos* del tablero.
5. Lee las últimas ~10 decisiones: los 10 ficheros de `docs/decisiones/` con mayor ID (`ls docs/decisiones | sort | tail -10`). El índice está en `docs/decisiones.md`.
6. Lee solo la sección de `docs/SPEC.md` del módulo en el que vas a trabajar, más los contratos (diseño del MVP §3 y §4).
7. Resume en 3-5 líneas qué vas a hacer y espera confirmación si toca más de un módulo.

Atajo: `/inicio` hace estos pasos. `/coger <ID>`, `/cierre` y `/decision` completan el flujo.

## Reglas de producto que el código no puede romper

1. **El LLM nunca calcula cifras.** Todo número (€, %, participaciones) sale del gestor de cartera o del motor de impacto. Claude solo redacta a partir de resultados de herramientas.
2. **Contexto, no órdenes.** Ningún texto generado dice "compra", "vende", "te recomiendo", "deberías invertir". Las oportunidades se expresan frente a las reglas del propio usuario (su plan, su DCA).
3. **Toda salida de agente pasa por el guardián** (`backend/app/agents/guardian.py`) antes de llegar al usuario. Sin excepciones, tampoco "para probar".
4. **Toda cifra mostrada es trazable**: lleva un `calc_id` que apunta a `calc_trace` con entradas, salidas y fuentes.
5. **Rangos, no cifras exactas** en impactos estimados (`impact_eur`, `low_eur`, `high_eur`, `confidence`).
6. Aviso de IA visible en la app y al empezar la voz (AI Act art. 50). Aviso "no es asesoramiento" en el panel.

## Modelo de trabajo: tareas y fases

No hay roles ni carpetas con dueño. Cualquiera hace cualquier tarea del pool de `docs/TABLERO.md` (IDs `T<fase>-<nn>`).

- **Fases.** 0 cimientos y contratos · 1 datos y motores · 2 experiencia e integración · 3 endurecer y entregar. Una fase está **cerrada** cuando todas sus tareas están en `main` con `make lint && make test` en verde.
- **Adelantar.** Se puede coger una tarea de la fase siguiente solo si **todas** sus dependencias están hechas. Si una tarea depende de otra, se hace antes la dependencia.
- **Claim.** Coger una tarea es un commit al tablero (`docs: claim T1-04`) **antes de empezar**. Si ya está cogida, se elige otra. Usa `/coger <ID>`.
- **Propiedad por tarea.** Mientras una tarea está en curso, quien la tiene es dueño de los ficheros de su columna *Ficheros que toca*. Otra sesión no los edita: si necesita algo de ellos, apunta un bloqueo en el tablero. No se coge una tarea cuyos ficheros solapen con los de otra en curso.
- **Excepciones a la propiedad:** `docs/decisiones/` (se crea un fichero nuevo por decisión) y tu propia fila del tablero.
- **Tablero: solo commits directos a `main` (excepción a "todo por PR").** `docs/TABLERO.md` se modifica únicamente con commits directos a `main`, nunca dentro de un PR, y el commit toca solo ese fichero. Mensaje `docs: claim|release|done|block|note T<x>-<nn>`: `claim`, `release` y `done` cambian la fila de la tarea (*Cogida por* y *Estado*); `block` apunta o cierra una fila de *Bloqueos* (y marca la tarea `⛔`); `note` actualiza *Notas para retomar* o *Peticiones de contrato* (y marca `🧪 en PR`). Flujo: `git pull --rebase` → comprobar (p. ej. que la tarea sigue libre) → commit → `git push` justo después. Si el push falla, se repite desde el pull. Excepción puntual: `docs: tablero rules` para cambios de reglas del propio tablero (la sección *Reglas* de `docs/TABLERO.md`), también directo a `main`. Todo lo demás va por PR.
- **Arquitectura (no es propiedad).** Los módulos de backend se llaman entre sí solo a través de su `service.py`. Nunca consultes las tablas de otro módulo directamente. Si necesitas algo de otro módulo que aún no existe, usa su mock (`*/mock.py` o `frontend/src/api/mocks/`).
- **Contratos.** `backend/app/schemas/` y `frontend/src/api/generated/` se cierran en la fase 0. Después solo se cambian con un PR propio (sin mezclar implementación), una fila en *Peticiones de contrato* y aviso al equipo. Añadir un campo opcional es aceptable; renombrar o quitar, no.
- **Decisiones.** Qué "Si da tiempo" entra lo decide el equipo en el checkpoint del martes 10 a las 18:00 y se apunta en una decisión nueva de `docs/decisiones/`.

## Comandos

```bash
make up          # docker compose up --build (db + backend + frontend)
make seed        # carga data/seed en la base de datos (carteras Laura y Javier)
make test        # pytest backend + vitest frontend
make lint        # ruff + mypy (backend), eslint + tsc (frontend)
make gen-api     # regenera tipos TS y mocks desde el backend; sube lo generado en el mismo PR (el CI falla si cambia)
make replay EVENT=bce-2025-06   # inyecta un evento del modo replay
make betas       # recalcula factor_beta desde data/prices
```

Antes de dar una tarea por terminada: `make lint && make test` en verde.

## Herramientas

Van en git (`.claude/settings.json`, `.claude/skills/`, `skills-lock.json`); ver D-033.

- **impeccable** (skill): UI en general: diseñar, criticar, pulir, auditar pantallas.
- **Emil Kowalski** (`emil-design-eng`, `review-animations`): motion y pulido fino de componentes.
- **playwright-cli** (skill + binario): para que el agente abra la app, la pruebe y haga capturas. No es `@playwright/test`, que se usa para los E2E de T3-02.
- **superpowers** (plugin): plan, TDD y debugging. Es pesado para 4 días: brainstorming y planes solo en tareas que tocan más de un módulo; en tareas pequeñas, directo.

Tras clonar, una vez: `bash scripts/setup-dev.sh` (instala las dependencias del frontend con `npm ci`, necesarias para `make gen-api`, y el binario y el navegador de playwright-cli) y aceptar los plugins al abrir Claude Code. Se puede repetir sin riesgo: solo reinstala el frontend si `node_modules` no está al día con `package-lock.json`.

## Convenciones de código

- **Idioma**: identificadores, nombres de fichero y commits en inglés. Textos visibles por el usuario, prompts de los agentes y documentación en español de España.
- **Python 3.12**, gestor `uv`. FastAPI, SQLAlchemy 2.0 (estilo tipado), Pydantic v2, Alembic. Type hints obligatorios; `mypy --strict` en `portfolio/`, `impact/` y `agents/guardian.py`.
- **Dinero y participaciones: `Decimal`**, nunca `float`. En BD `NUMERIC(18,2)` para euros y `NUMERIC(20,8)` para participaciones y precios. Redondeo `ROUND_HALF_EVEN` solo al presentar. pandas/numpy solo dentro de `impact/` para calcular betas; la salida se convierte a `Decimal`.
- **Fechas** siempre con zona horaria (UTC en BD). Usa `app.core.clock.now()`, nunca `datetime.now()`: en modo demo el reloj se puede fijar.
- **TypeScript estricto**, React + Vite, componentes funcionales. Llamadas al backend solo desde `src/api/` con los tipos generados.
- Ficheros < 300 líneas; funciones puras en los motores (entrada → salida, sin BD), la BD se toca en `repository.py`.
- Sin dependencias nuevas sin anotarlo en una decisión (`docs/decisiones/`).
- Secretos solo en `.env` (nunca en el repo). Si añades una variable, añádela también a `.env.example`.
- **Escribe los ficheros con Edit/Write, nunca con el shell de Windows** (`echo`, heredocs, `sed -i`, `python -` leyendo de la entrada estándar): la consola rompe la codificación de tildes y símbolos (`Ã`, `Â`).

## Tests

- `portfolio/` e `impact/`: test primero. Casos dorados con las carteras de Laura y Javier en `backend/tests/golden/`.
- `agents/guardian.py`: un test por cada patrón prohibido y por la comprobación de cifras.
- Los tests no llaman a APIs externas: Claude y ElevenLabs se mockean (`tests/fakes/`). Hay un marcador `@pytest.mark.live` para los que sí, que no corre en CI.

## Git

- Rama por tarea: `t<fase>-<nn>/<descripcion-corta>` (p. ej. `t1-13/impact-fx-split`). PR pequeño a `main`, CI en verde y un revisor del equipo (vale con un vistazo de 5 minutos). El merge lo hace quien abre el PR, tras la aprobación.
- Commits: Conventional Commits (`feat(impact): ...`, `fix(portfolio): ...`, `docs: ...`). Los cambios del tablero usan `docs: claim|release|done|block|note T<x>-<nn>` y van directos a `main`, nunca en un PR (ver arriba).
- **Decisiones: un fichero cada una.** Cada decisión es `docs/decisiones/D-NNN-slug.md` (ID + slug corto del título, en minúsculas y sin tildes). Las nuevas se crean como `docs/decisiones/D-XXX-<slug>.md` (`D-XXX-a-<slug>.md`, `D-XXX-b-<slug>.md`… si hay varias en la misma rama), con `### D-XXX · Título` en la primera línea. `docs/decisiones.md` solo tiene la cabecera y un índice **generado**: no lo edites (el CI lo comprueba). Cambiar el *Estado* de una antigua es editar su fichero; el índice lo recoge solo.
- **IDs de decisiones.** La Action `renumber-decisions` (`scripts/renumber_decisions.py`) renombra el fichero, cambia el ID dentro y regenera el índice al entrar en `main`. No las numeres a mano. La Action solo sustituye `D-XXX` en las decisiones que numera y en los ficheros que cambia ese mismo PR. **Fuera del propio PR** (por ejemplo, en el tablero), una decisión aún sin mergear se cita **por título**, nunca como `D-XXX`: no se renumeraría o, peor, se confundiría con la de otro PR.
- Nunca `push --force` a `main`. No mezcles en un PR cambios de contrato con cambios de implementación.
- **Congelación**: el miércoles 11 a las 16:00 solo se aceptan fixes. Entrega antes de las 21:00 (cierre oficial 23:59). Lo que se entrega es el ZIP de `main`.

## Al terminar una sesión (o antes de `/clear`)

1. Actualiza en `docs/TABLERO.md` la subsección de tu tarea en *Notas para retomar* (qué estabas haciendo, siguiente paso exacto, ficheros tocados) con un commit directo a `main`: `docs: note T<x>-<nn>`. Si la tarea ya está en `main`, márcala `✅ hecho` con `docs: done T<x>-<nn>` y borra sus notas. Si la abandonas, `docs: release T<x>-<nn>`.
2. Si se tomó una decisión de diseño, crea su fichero `docs/decisiones/D-XXX-<slug>.md` con el ID provisional `D-XXX` (con `/decision`). La Action le pone el ID real y actualiza el índice al entrar en `main` (ver *Git*).
3. Si cambió algo de arquitectura, contrato o modelo de datos, actualiza `docs/SPEC.md`.
4. Commit de los docs (menos el tablero, que va aparte en un commit directo a `main`) junto al código, en tu rama (`docs: update notas T<x>-<nn>`).

## Qué NO hacer

- No generes datos financieros "realistas" inventados en código de producción. Los datos de ejemplo viven en `data/seed/` y llevan la marca `"illustrative": true`.
- No pongas cifras en los prompts como ejemplo de respuesta (el modelo las copia). Usa `<IMPORTE>` como marcador.
- No añadas features fuera de la tabla de `docs/INGENIERIA.md` §4. Si parece necesaria, se propone en el tablero.
- No edites `docs/decisiones.md` (el índice es generado) ni reescribas una decisión antigua: solo se añade un fichero nuevo en `docs/decisiones/`, y de las antiguas solo se cambia el campo *Estado*.

## Mapa de documentos

| Documento | Para qué |
| --- | --- |
| `docs/kairos-spec.md` | Producto (no se cambia). Orden de autoridad: producto > diseño del MVP > resto |
| `docs/INGENIERIA.md` | Requisitos, casos de uso, diagramas, trazabilidad, plan de pruebas |
| `docs/superpowers/specs/2026-11-08-kairos-mvp-design.md` | Diseño técnico del MVP (aprobado): contratos exactos, fases y tareas. Manda sobre `SPEC.md` |
| `docs/SPEC.md` | Stack, estructura del repo, modelo de datos, API, algoritmos, agentes |
| `docs/decisiones/` | Registro de decisiones (qué, cuándo, por qué): un fichero `D-NNN-slug.md` por decisión. `docs/decisiones.md` es la cabecera y el índice generado |
| `docs/TABLERO.md` | Pool de tareas por fase, quién ha cogido cada una, bloqueos, notas para retomar |
