---
description: Registra una decisión de diseño en docs/decisiones.md
argument-hint: <título corto de la decisión>
---

Registra una decisión en `docs/decisiones.md`. Título propuesto: $ARGUMENTS (si está vacío, dedúcelo de la conversación y confírmalo).

Una decisión merece entrada si cambia un contrato o el modelo de datos, añade una dependencia, afecta a otra tarea, o se va a olvidar en 2 horas.

1. `git pull --rebase`, para ver las últimas entradas.
2. Lee el índice y las últimas entradas. **No asignes un ID real**: usa el provisional `D-XXX` (si añades varias en la misma rama, `D-XXX-a`, `D-XXX-b`…). El ID correlativo lo asigna quien mergea el PR, justo antes de mergear. Comprueba que no existe una entrada que ya cubra esto; si la hay y cambia, crea una nueva y en la antigua cambia **solo** el campo *Estado* a `Sustituida por D-XXX` (se sustituye por el ID real al mergear).
3. **Añade al final** del fichero (nunca reescribas entradas) con la plantilla:

```
### D-XXX · Título corto
- Fecha: AAAA-MM-DD HH:MM · Autor: nombre · Estado: Propuesta
- Contexto: qué problema había.
- Decisión: qué se hace.
- Motivo: por qué esto y no otra cosa.
- Alternativas descartadas: ...
- Consecuencias: qué cambia, quién se ve afectado, ficheros.
```

4. Añade la fila al **índice** de arriba (`D-XXX` · fecha · título · estado). Si otros ficheros citan la decisión (código, `SPEC.md`, tablero), cita también `D-XXX`.
5. `docs/decisiones.md` es una excepción a la propiedad por tarea: cualquiera puede añadir. Va en el PR de tu tarea o, si es suelta, en un PR `docs:` pequeño.
6. Si la decisión toca `SPEC.md` o un contrato, dilo al humano; los contratos solo se cambian con PR propio y aviso al equipo.
7. **Al mergear** (lo hace quien mergea el PR, no quien escribe la decisión): `git fetch`, busca el último ID de `main` y sustituye `D-XXX` por el siguiente libre en la entrada, el índice, las referencias y la descripción del PR. Comprueba que no quedan `D-XXX` ni IDs repetidos.
