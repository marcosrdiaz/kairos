# CLAUDE.md — KAIROS

KAIROS traduce eventos financieros (BCE, petróleo, resultados, divisas) al impacto en euros sobre la cartera de un inversor particular. Hackathon Hack Finance (BEST UC3M), 4 días, 5 personas trabajando en paralelo, cada una con su propia sesión de Claude Code.

Este fichero se carga en todas las sesiones. Es corto a propósito: el detalle está en `docs/`.

## Al empezar una sesión (o tras `/clear`)

1. Pregunta al humano **cómo se llama** (Manu, Jaime, Marcos, Alons o Javi) y si va a **continuar una tarea suya en curso** o a **coger una nueva**.
2. Si continúa una tarea: lee su fila y su subsección en *Notas para retomar* de `docs/TABLERO.md`.
3. Si coge una nueva: lista las tareas **disponibles de la fase actual** (la primera fase no cerrada): estado `⬜`, sin nadie en *Cogida por*, con todas sus dependencias hechas y sin ficheros en común con una tarea en curso. Que elija una y cógela con `/coger <ID>` antes de empezar.
4. Lee la tabla de *Bloqueos* del tablero.
5. Lee las últimas ~10 entradas de `docs/decisiones.md`.
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
- **Excepciones a la propiedad:** `docs/decisiones.md` (solo se añade al final) y tu propia fila del tablero.
- **Commits directos a `main` (excepción a "todo por PR").** Solo si tocan únicamente `docs/TABLERO.md` y el mensaje es `docs: claim|release|done T<x>-<nn>`. Flujo: `git pull --rebase` → comprobar que la tarea sigue libre → commit → `git push`. Si el push falla, se repite desde el pull. Todo lo demás va por PR.
- **Arquitectura (no es propiedad).** Los módulos de backend se llaman entre sí solo a través de su `service.py`. Nunca consultes las tablas de otro módulo directamente. Si necesitas algo de otro módulo que aún no existe, usa su mock (`*/mock.py` o `frontend/src/api/mocks/`).
- **Contratos.** `backend/app/schemas/` y `frontend/src/api/generated/` se cierran en la fase 0. Después solo se cambian con un PR propio (sin mezclar implementación), una fila en *Peticiones de contrato* y aviso al equipo. Añadir un campo opcional es aceptable; renombrar o quitar, no.
- **Decisiones.** Qué "Si da tiempo" entra lo decide el equipo en el checkpoint del martes 10 a las 18:00 y se apunta en `docs/decisiones.md`.

## Comandos

```bash
make up          # docker compose up --build (db + backend + frontend)
make seed        # carga data/seed en la base de datos (carteras Laura y Javier)
make test        # pytest backend + vitest frontend
make lint        # ruff + mypy (backend), eslint + tsc (frontend)
make gen-api     # regenera tipos TS desde el OpenAPI del backend
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

Tras clonar, una vez: `bash scripts/setup-dev.sh` (instala el binario y el navegador de playwright-cli) y aceptar los plugins al abrir Claude Code.

## Convenciones de código

- **Idioma**: identificadores, nombres de fichero y commits en inglés. Textos visibles por el usuario, prompts de los agentes y documentación en español de España.
- **Python 3.12**, gestor `uv`. FastAPI, SQLAlchemy 2.0 (estilo tipado), Pydantic v2, Alembic. Type hints obligatorios; `mypy --strict` en `portfolio/`, `impact/` y `agents/guardian.py`.
- **Dinero y participaciones: `Decimal`**, nunca `float`. En BD `NUMERIC(18,2)` para euros y `NUMERIC(20,8)` para participaciones y precios. Redondeo `ROUND_HALF_EVEN` solo al presentar. pandas/numpy solo dentro de `impact/` para calcular betas; la salida se convierte a `Decimal`.
- **Fechas** siempre con zona horaria (UTC en BD). Usa `app.core.clock.now()`, nunca `datetime.now()`: en modo demo el reloj se puede fijar.
- **TypeScript estricto**, React + Vite, componentes funcionales. Llamadas al backend solo desde `src/api/` con los tipos generados.
- Ficheros < 300 líneas; funciones puras en los motores (entrada → salida, sin BD), la BD se toca en `repository.py`.
- Sin dependencias nuevas sin anotarlo en `docs/decisiones.md`.
- Secretos solo en `.env` (nunca en el repo). Si añades una variable, añádela también a `.env.example`.

## Tests

- `portfolio/` e `impact/`: test primero. Casos dorados con las carteras de Laura y Javier en `backend/tests/golden/`.
- `agents/guardian.py`: un test por cada patrón prohibido y por la comprobación de cifras.
- Los tests no llaman a APIs externas: Claude y ElevenLabs se mockean (`tests/fakes/`). Hay un marcador `@pytest.mark.live` para los que sí, que no corre en CI.

## Git

- Rama por tarea: `t<fase>-<nn>/<descripcion-corta>` (p. ej. `t1-13/impact-fx-split`). PR pequeño a `main`, CI en verde y un revisor del equipo (vale con un vistazo de 5 minutos). El merge lo hace quien abre el PR, tras la aprobación.
- Commits: Conventional Commits (`feat(impact): ...`, `fix(portfolio): ...`, `docs: ...`). Los claims usan `docs: claim|release|done T<x>-<nn>` y pueden ir directos a `main` (ver arriba).
- **IDs de decisiones.** En la rama las decisiones llevan `D-XXX`. Quien mergea el PR, justo antes, sustituye `D-XXX` por el siguiente ID libre según `main` (entrada, índice, referencias y descripción del PR).
- Nunca `push --force` a `main`. No mezcles en un PR cambios de contrato con cambios de implementación.
- **Congelación**: el miércoles 11 a las 16:00 solo se aceptan fixes. Entrega antes de las 21:00 (cierre oficial 23:59). Lo que se entrega es el ZIP de `main`.

## Al terminar una sesión (o antes de `/clear`)

1. Actualiza en `docs/TABLERO.md` la subsección de tu tarea en *Notas para retomar* (qué estabas haciendo, siguiente paso exacto, ficheros tocados). Si la tarea ya está en `main`, márcala `✅ hecho` con `docs: done T<x>-<nn>` y borra sus notas. Si la abandonas, `docs: release T<x>-<nn>`.
2. Si se tomó una decisión de diseño, añádela a `docs/decisiones.md` con el ID provisional `D-XXX` (entrada e índice). El ID real lo pone quien mergea el PR (ver *Git*).
3. Si cambió algo de arquitectura, contrato o modelo de datos, actualiza `docs/SPEC.md`.
4. Commit de los docs junto al código (`docs: update notas T<x>-<nn>`).

## Qué NO hacer

- No generes datos financieros "realistas" inventados en código de producción. Los datos de ejemplo viven en `data/seed/` y llevan la marca `"illustrative": true`.
- No pongas cifras en los prompts como ejemplo de respuesta (el modelo las copia). Usa `<IMPORTE>` como marcador.
- No añadas features fuera de la tabla de `docs/INGENIERIA.md` §4. Si parece necesaria, se propone en el tablero.
- No toques `docs/decisiones.md` salvo para añadir al final (solo se cambia el campo *Estado* de entradas anteriores).

## Mapa de documentos

| Documento | Para qué |
| --- | --- |
| `docs/kairos-spec.md` | Producto (no se cambia). Orden de autoridad: producto > diseño del MVP > resto |
| `docs/INGENIERIA.md` | Requisitos, casos de uso, diagramas, trazabilidad, plan de pruebas |
| `docs/superpowers/specs/2026-11-08-kairos-mvp-design.md` | Diseño técnico del MVP (aprobado): contratos exactos, fases y tareas. Manda sobre `SPEC.md` |
| `docs/SPEC.md` | Stack, estructura del repo, modelo de datos, API, algoritmos, agentes |
| `docs/decisiones.md` | Registro de decisiones (qué, cuándo, por qué) |
| `docs/TABLERO.md` | Pool de tareas por fase, quién ha cogido cada una, bloqueos, notas para retomar |
