---
description: Cierre de sesión: notas para retomar, estado de la tarea y decisiones pendientes
---

Haz los pasos de "Al terminar una sesión" de `CLAUDE.md` para la tarea en la que has trabajado.

1. Comprueba el estado real con `git status` y `git log` de tu rama, y con `make lint && make test` si hay código.
2. En `docs/TABLERO.md`, actualiza la subsección de tu tarea en *Notas para retomar* (créala con la plantilla si no existe):
   - **Qué estaba haciendo.**
   - **Siguiente paso exacto.**
   - **Ficheros tocados.**
3. Ajusta el estado de la fila de tu tarea: `🔄 en curso`, `🧪 en PR` (con el enlace del PR en las notas) o `⛔ bloqueado` (y añade la fila en *Bloqueos*).
4. Si la tarea está terminada y **ya en `main`** con `make lint && make test` en verde: márcala `✅ hecho`, borra sus notas y usa el mensaje `docs: done <ID>`. Si la abandonas: `docs: release <ID>` (vuelve a `⬜` y `—`).
5. Si se tomó una decisión de diseño que aún no está registrada, ejecuta `/decision`.
6. Si cambió arquitectura, contrato o modelo de datos, actualiza `docs/SPEC.md`.
7. Commit de los docs junto al código en tu rama (`docs: update notas <ID>`). Los cambios que toquen solo la fila del tablero para `claim|release|done` pueden ir directos a `main` siguiendo el flujo de `/coger` (`git pull --rebase` → comprobar → commit → `git push`); todo lo demás, por PR.
8. Dile al humano en 3 líneas cómo queda la tarea y que ya puede hacer `/clear`.
