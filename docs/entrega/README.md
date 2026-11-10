# Entrega: PDF de una cara y presentación (T6-02)

| Fichero | Qué es |
| --- | --- |
| `KAIROS-una-cara.pdf` | PDF de una cara (A4): problema, solución, valor diferencial, la misma noticia en dos carteras, negocio y confianza |
| `KAIROS-presentacion.pptx` | Presentación para el jurado: 10 diapositivas con notas de orador. La 6 es la de arquitectura |
| `fuentes/` | Lo necesario para regenerar los dos y recalcular las cifras |

**Pendiente: revisión del equipo** (criterio de T6-02). Los textos y el orden de las diapositivas se pueden cambiar; las cifras, solo recalculándolas (ver abajo).

## De dónde salen las cifras

Ninguna cifra está escrita a mano: las calcula el backend (regla 1 de `CLAUDE.md`). Se obtuvieron el 10-nov-2026 con `fuentes/pitch_figures.py` sobre una base de datos recién creada en modo demo, sin claves de Claude ni ElevenLabs: `alembic upgrade head`, `scripts/seed_db.py`, `scripts/compute_betas.py` (75 betas) y replay de los 3 eventos. Precios de cierre reales hasta el 6-nov-2026 (`data/prices`, `data/factors`). Las carteras de Laura y Javier son de ejemplo (`illustrative`).

**Radiografía de Laura** (antes de los eventos, como en el paso 2 del guion): 63,7 % en EE. UU., 25,9 % en 7 empresas y 76,0 % en renta variable. Coincide con las cifras de *Notas para retomar* del tablero.

**Impacto de cada evento** (`GET /portfolios/{id}/events`; rango redondeado al euro):

| Evento | Laura (42.364 €) | Javier (180.000 €) |
| --- | --- | --- |
| BCE, 5 jun 2025 | −89,29 a −72,89 € · −0,19 % · confianza alta | −242,83 a −206,25 € · −0,12 % · media |
| Petróleo, 13 jun 2025 | −250,34 a −206,58 € · −0,54 % · alta | −450,60 a −352,40 € · −0,22 % · media |
| NVIDIA, 26 feb 2025 | −349,11 a −325,01 € · −0,80 % · alta | −272,81 a −205,77 € · −0,13 % · media |

**Otras cifras citadas:**
- Voz: primera palabra hablada en 1,7 s de mediana, por debajo de 2 s en 9 de 10 intentos. Fuente: la decisión de latencia de voz de T2-16 (`docs/decisiones/D-071-latencia-voz-t2-16.md`).
- Órdenes: 0 en 30 preguntas con Claude real, 10 de ellas trampa. Fuente: `docs/decisiones/D-088-evaluacion-30-preguntas.md`.
- Tests: más de 2.200 (1.845 de backend y 363 de frontend el 10-nov-2026).
- Datos de mercado del problema (CNMV, Encuesta Financiera de las Familias, ING): `docs/kairos-spec.md`, sección *Problema*, con sus enlaces.

Si cambian los datos, los precios, las betas o el motor, hay que recalcular las cifras y actualizar `fuentes/deck.js`, `fuentes/onepager.html` y esta tabla antes de entregar.

## Cómo regenerar

Desde `backend/`, con un SQLite temporal:

```bash
export DATABASE_URL=sqlite:///$TEMP/kairos_pitch.db DEMO_MODE=true MARKET_DATA_PROVIDER=offline ANTHROPIC_API_KEY= ELEVENLABS_API_KEY=
uv run alembic upgrade head && uv run python ../scripts/seed_db.py && uv run python ../scripts/compute_betas.py
uv run python ../docs/entrega/fuentes/pitch_figures.py
```

- **Presentación:** `node fuentes/deck.js KAIROS-presentacion.pptx` (necesita `pptxgenjs@3.12.0`, instalado aparte: no es una dependencia del proyecto) y después `python fuentes/strip_dirs.py KAIROS-presentacion.pptx`, que quita las entradas de carpeta del ZIP.
- **PDF de una cara:** imprimir `fuentes/onepager.html` a PDF en A4 sin encabezados ni pies, por ejemplo `msedge --headless=new --no-pdf-header-footer --print-to-pdf=KAIROS-una-cara.pdf fuentes/onepager.html`.

Fuentes tipográficas: Cambria para los títulos y Calibri para el texto, que vienen con Office. Colores: los tokens `--kairos-*` de la app.
