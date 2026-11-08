### D-032 · Avisos mínimos (`event_impact`, 2 por semana ISO) pasan a MVP
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: RF-23 era "S" en `INGENIERIA.md`, pero el paso 3 del guion (replay → Atento + aviso) y T2-08 dependen de los avisos de tipo `event_impact`.
- Decisión: RF-23 pasa a M en versión mínima: avisos `kind=event_impact` con `score = |impact_eur| / max(150, 0,005 · total)`, aviso si `score ≥ 1`, y límite de 2 por semana ISO y cartera según `clock.now()`. `dca_pending` y `drift` siguen en "Si da tiempo". Contrato en el diseño §4.4.
- Consecuencias: `INGENIERIA.md` (RF-23 y trazabilidad del paso 3) actualizado; T2-08 es MVP.
