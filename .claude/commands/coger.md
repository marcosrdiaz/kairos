---
description: Coge una tarea del tablero (claim) si está libre y con dependencias hechas
argument-hint: <ID de tarea, p. ej. T1-04>
---

Vas a coger la tarea **$ARGUMENTS** de `docs/TABLERO.md`. Si no hay ID, pide uno (o lista las disponibles como en `/inicio`).

Excepción explícita a "todo por PR": el tablero solo se modifica con commits **directos a `main`**, nunca dentro de un PR. Un claim toca únicamente `docs/TABLERO.md` y su mensaje es `docs: claim T<x>-<nn>` (los demás tipos son `release`, `done`, `block` y `note`). Cualquier otro cambio va por PR.

Flujo (si el `push` falla, repite desde el paso 1):

1. `git status`: si hay cambios sin guardar que no sean tuyos, para y avisa al humano. Si no estás en `main`, haz el claim desde un worktree o cambia a `main` con el humano; no mezcles el claim con otra rama.
2. `git pull --rebase` en `main`.
3. Busca la tarea en el tablero y comprueba **todo** esto. Si falla algo, para, dilo y propón otra tarea:
   - **Existe** el ID.
   - **Está libre**: estado `⬜ pendiente` y *Cogida por* vacío (`—`).
   - **Dependencias hechas**: cada ID de *Depende de* está en `✅ hecho`. Las marcadas `(b)` son blandas y no bloquean, pero avisa.
   - **Fase**: es de la fase actual (la primera no cerrada) o, si es de la siguiente, todas sus dependencias están hechas (adelantar).
   - **Sin solape de ficheros**: ninguna tarea `🔄 en curso`, `🧪 en PR` o `⛔ bloqueado` declara ficheros en común con los de esta.
4. Pregunta al humano su nombre si no lo has oído en esta sesión.
5. Edita **solo** la fila de esa tarea en `docs/TABLERO.md`: *Cogida por* = su nombre, *Estado* = `🔄 en curso`. No toques nada más.
6. Commit con exactamente `docs: claim <ID>` (con la atribución de Claude al final del mensaje) y `git push` **justo después**.
7. Si el push se rechaza: `git pull --rebase`, vuelve al paso 3 (puede que alguien se te haya adelantado) y repite.
8. Con el claim hecho, ve a una rama `t<fase>-<nn>/<descripcion-corta>` y sigue el criterio de hecho de la tarea. Recuerda: eres dueño solo de los ficheros que la tarea declara.

Para soltar una tarea sin terminarla: mismo flujo con `docs: release <ID>` (vuelve a `⬜` y `—`, y borra o conserva sus *Notas para retomar* según convenga).
