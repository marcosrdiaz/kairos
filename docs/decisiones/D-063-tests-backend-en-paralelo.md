### D-063 · Tests del backend en paralelo con pytest-xdist (T1-23)
- Fecha: 2026-11-09 · Autor: Alons · Estado: Propuesta
- Contexto: `make test` tardaba unos 2 minutos en local (1069 tests). Medido con `--durations`: 59 s de *setup* de fixtures, 25 s de *teardown* y solo 24 s dentro de los tests. Ningún test es lento por sí solo: el coste es el `create_all`, el seed y la app que se repiten en cada test, además del `drop_all` del final.
- Decisión:
  - Nueva dependencia de desarrollo `pytest-xdist` (y su dependencia `execnet`). `make test-backend` ejecuta `pytest -n auto`, con un proceso por núcleo. El CI hereda el cambio porque llama a `make test`.
  - `-n auto` va en el `Makefile`, no en `addopts`: así `uv run pytest <fichero>` sigue en serie y arranca sin la espera de los procesos.
  - La fixture `db` deja de hacer `drop_all` al terminar: el SQLite está en el `tmp_path` del test y se descarta entero.
- Motivo: los tests ya están aislados (cada uno usa su propio SQLite en `tmp_path` y el reloj y la configuración se reinician), así que se pueden paralelizar sin tocarlos. En local, con 12 núcleos, el backend pasa de 119 s a 41 s.
- Alternativas descartadas: un SQLite plantilla con tablas y seed por sesión, copiado en cada test (ataca el *setup*, pero cambia las fixtures de las que dependen todas las tareas; se puede añadir encima si hace falta); marcar tests como lentos y saltarlos (deja huecos sin probar en `make test`).
- Consecuencias: un test nuevo no puede depender del orden de ejecución ni escribir fuera de `tmp_path` (por ejemplo, en `data/` o en el repo), porque correría a la vez que otros. Los fallos salen con el nombre del worker (`[gw3]`); para depurar uno, se relanza ese fichero sin `-n`.
