### D-017 · Claims de tareas directos a `main`
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: dos personas pueden coger la misma tarea si el claim va por PR.
- Decisión: excepción explícita a "todo por PR". Solo se permiten commits directos a `main` que toquen únicamente `docs/TABLERO.md` y cuyo mensaje sea `docs: claim|release|done T<x>-<nn>`. Flujo: `git pull --rebase` → comprobar que la tarea sigue libre → commit → `git push`; si el push falla, se repite desde el pull.
- Motivo: un claim solo vale si es inmediato y visible para todos.
- Consecuencias: `CLAUDE.md` y `/coger` lo recogen. El repositorio es privado en plan gratuito de GitHub y no admite protección de rama (la API devuelve 403), así que el push directo no está bloqueado y la regla se cumple por convención.
