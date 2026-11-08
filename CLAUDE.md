# CLAUDE.md — KAIROS

KAIROS traduce eventos financieros (BCE, petróleo, resultados, divisas) al impacto en euros sobre la cartera de un inversor particular. Hackathon Hack Finance (BEST UC3M), 4 días, 5 personas trabajando en paralelo, cada una con su propia sesión de Claude Code.

Este fichero se carga en todas las sesiones. Es corto a propósito: el detalle está en `docs/`.

## Al empezar una sesión (o tras `/clear`)

1. Pregunta al humano quién es (P1–P5) si no lo ha dicho. Su rol y sus carpetas están en `docs/TABLERO.md` → *Equipo*.
2. Lee su sección en `docs/TABLERO.md` (*En curso*, *Notas para retomar*) y la tabla de *Bloqueos*.
3. Lee las últimas ~10 entradas de `docs/decisiones.md`.
4. Lee solo la sección de `docs/SPEC.md` del módulo en el que vas a trabajar, más *Contratos* (§5).
5. Resume en 3-5 líneas qué vas a hacer y espera confirmación si toca más de un módulo.

Atajo: `/inicio` hace estos pasos. `/cierre` hace los de salida.

## Reglas de producto que el código no puede romper

1. **El LLM nunca calcula cifras.** Todo número (€, %, participaciones) sale del gestor de cartera o del motor de impacto. Claude solo redacta a partir de resultados de herramientas.
2. **Contexto, no órdenes.** Ningún texto generado dice "compra", "vende", "te recomiendo", "deberías invertir". Las oportunidades se expresan frente a las reglas del propio usuario (su plan, su DCA).
3. **Toda salida de agente pasa por el guardián** (`backend/app/agents/guardian.py`) antes de llegar al usuario. Sin excepciones, tampoco "para probar".
4. **Toda cifra mostrada es trazable**: lleva un `calc_id` que apunta a `calc_trace` con entradas, salidas y fuentes.
5. **Rangos, no cifras exactas** en impactos estimados (`impact_eur`, `low_eur`, `high_eur`, `confidence`).
6. Aviso de IA visible en la app y al empezar la voz (AI Act art. 50). Aviso "no es asesoramiento" en el panel.

## Propiedad del código

Cada carpeta tiene un dueño (tabla en `docs/TABLERO.md`). Reglas:

- Solo editas las carpetas del dueño con el que trabajas.
- `backend/app/schemas/` y `frontend/src/api/generated/` son **contratos compartidos**: no se cambian sin abrir una fila en *Peticiones de contrato* del tablero y avisar al humano. Añadir un campo opcional es aceptable; renombrar o quitar, no.
- Si necesitas algo de otro módulo que no existe, usa su mock (`*/mock.py` o `frontend/src/api/mocks/`) y apunta el bloqueo en el tablero. No lo implementes tú.
- Los módulos de backend se llaman entre sí solo a través de su `service.py`. Nunca consultes las tablas de otro módulo directamente.

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

- Rama por tarea: `p<N>/<descripcion-corta>` (p. ej. `p2/impact-fx-split`). PR pequeño a `main`, CI en verde, un revisor del equipo (vale con un vistazo de 5 minutos).
- Commits: Conventional Commits (`feat(impact): ...`, `fix(portfolio): ...`, `docs: ...`).
- Nunca `push --force` a `main`. No mezcles en un PR cambios de contrato con cambios de implementación.
- **Congelación**: el miércoles 11 a las 16:00 solo se aceptan fixes. Entrega antes de las 21:00 (cierre oficial 23:59). Lo que se entrega es el ZIP de `main`.

## Al terminar una sesión (o antes de `/clear`)

1. Actualiza tu sección de `docs/TABLERO.md`: mueve tareas a *Hecho*, escribe *Notas para retomar* (qué estabas haciendo, siguiente paso exacto, ficheros tocados).
2. Si se tomó una decisión de diseño, añádela a `docs/decisiones.md` con tu rango de ID.
3. Si cambió algo de arquitectura, contrato o modelo de datos, actualiza `docs/SPEC.md`.
4. Commit de los docs junto al código (`docs: update tablero P<N>`).

## Qué NO hacer

- No generes datos financieros "realistas" inventados en código de producción. Los datos de ejemplo viven en `data/seed/` y llevan la marca `"illustrative": true`.
- No pongas cifras en los prompts como ejemplo de respuesta (el modelo las copia). Usa `<IMPORTE>` como marcador.
- No añadas features fuera de la tabla de `docs/INGENIERIA.md` §4. Si parece necesaria, se propone en el tablero.
- No toques `docs/decisiones.md` salvo para añadir al final (solo se cambia el campo *Estado* de entradas anteriores).

## Mapa de documentos

| Documento | Para qué |
| --- | --- |
| `docs/INGENIERIA.md` | Requisitos, casos de uso, diagramas, trazabilidad, plan de pruebas |
| `docs/SPEC.md` | Stack, estructura del repo, modelo de datos, API, algoritmos, agentes |
| `docs/decisiones.md` | Registro de decisiones (qué, cuándo, por qué) |
| `docs/TABLERO.md` | Quién hace qué, estado, bloqueos, notas para retomar |
