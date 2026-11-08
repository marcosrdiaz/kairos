---
description: Arranque de sesión: quién eres, qué tarea continúas o coges, y contexto mínimo
---

Haz los pasos de "Al empezar una sesión" de `CLAUDE.md`. No leas más de lo necesario.

1. Pregunta al humano **cómo se llama** (Manu, Jaime, Marcos, Alons o Javi) y si va a **continuar una tarea suya en curso** o a **coger una nueva**.
2. Haz `git pull --rebase` y lee `docs/TABLERO.md`.
3. **Si continúa una tarea**: localiza sus tareas con *Cogida por* = su nombre y estado `🔄`, `🧪` o `⛔`. Si hay varias, pregunta cuál. Lee su criterio, sus ficheros y su subsección de *Notas para retomar*.
4. **Si coge una nueva**: determina la fase actual (la primera con alguna tarea sin `✅`) y lista las tareas **disponibles**: `⬜`, *Cogida por* vacío, todas las dependencias (sin contar las `(b)`) en `✅`, y ficheros sin solape con tareas en curso. Si no queda ninguna en la fase actual, lista las de la siguiente cuyas dependencias estén hechas (adelantar). Muestra ID, tarea, criterio y ficheros. Cuando elija, ejecuta el flujo de `/coger <ID>`.
5. Lee la tabla de *Bloqueos* y las últimas ~10 decisiones: los 10 ficheros de `docs/decisiones/` con mayor ID (`ls docs/decisiones | sort | tail -10`). El índice completo está en `docs/decisiones.md`.
6. Lee solo la sección de `docs/SPEC.md` del módulo de la tarea, más los contratos relevantes (`docs/superpowers/specs/2026-11-08-kairos-mvp-design.md` §3 y §4).
7. Resume en 3-5 líneas qué vas a hacer (tarea, ficheros, primer paso) y **espera confirmación** si toca más de un módulo.
