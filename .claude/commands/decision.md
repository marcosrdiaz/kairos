---
description: Registra una decisión de diseño como un fichero nuevo en docs/decisiones/
argument-hint: <título corto de la decisión>
---

Registra una decisión creando **un fichero nuevo** en `docs/decisiones/`. Título propuesto: $ARGUMENTS (si está vacío, dedúcelo de la conversación y confírmalo).

Una decisión merece entrada si cambia un contrato o el modelo de datos, añade una dependencia, afecta a otra tarea, o se va a olvidar en 2 horas.

1. `git pull --rebase`, para ver las últimas decisiones.
2. Lee las últimas decisiones: los 10 ficheros de `docs/decisiones/` con mayor ID (`ls docs/decisiones | sort | tail -10`). El índice completo está en `docs/decisiones.md`. Comprueba que no existe una que ya cubra esto; si la hay y cambia, crea una nueva y en el fichero de la antigua cambia **solo** el campo *Estado* a `Sustituida por D-XXX` (la Action sustituye `D-XXX` por el ID real, siempre que el fichero de la antigua vaya en el mismo PR).
3. **Crea el fichero** `docs/decisiones/D-XXX-<slug>.md`, donde `<slug>` es un resumen corto del título en minúsculas, sin tildes y con guiones (p. ej. `D-XXX-reloj-inyectable.md`). **No asignes un ID real**: usa el provisional `D-XXX`. Si añades varias en la misma rama, `D-XXX-a-<slug>.md`, `D-XXX-b-<slug>.md`… (y `### D-XXX-a · …` dentro). La Action `renumber-decisions` renombra el fichero y cambia el ID al entrar en `main`; no lo toques a mano. Contenido, con esta plantilla (la primera línea y la de *Fecha* son obligatorias):

```
### D-XXX · Título corto
- Fecha: AAAA-MM-DD HH:MM · Autor: nombre · Estado: Propuesta
- Contexto: qué problema había.
- Decisión: qué se hace.
- Motivo: por qué esto y no otra cosa.
- Alternativas descartadas: ...
- Consecuencias: qué cambia, quién se ve afectado, ficheros.
```

4. **No toques `docs/decisiones.md`**: el índice se genera solo (el CI falla si lo editas a mano). Si otros ficheros **del mismo PR** (código, `SPEC.md`) citan la decisión, cita también `D-XXX` (o `D-XXX-a`). Fuera del PR, por ejemplo en el tablero, que no va en PRs, cítala **por título** (p. ej. «Modelo de datos y migración inicial (T1-01)»), nunca como `D-XXX`: la Action solo renumera los ficheros del propio PR.
5. `docs/decisiones/` es una excepción a la propiedad por tarea: cualquiera puede añadir. Va en el PR de tu tarea o, si es suelta, en un PR `docs:` pequeño. Dos PRs que añaden decisiones no se pisan, porque cada una es un fichero distinto.
6. Si la decisión toca `SPEC.md` o un contrato, dilo al humano; los contratos solo se cambian con PR propio y aviso al equipo.
7. **Al mergear** no hay nada que hacer: la Action `renumber-decisions` asigna el ID real en `main` (fichero, cabecera, referencias del PR e índice). No renumeres en el PR.
