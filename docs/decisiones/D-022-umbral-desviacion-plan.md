### D-022 · Umbral de desviación del plan: `drift_threshold` = 0,10
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: Laura (RV 76 %, objetivo 70 %) arrancaba en "Revisa tu plan" con el umbral de 5 pp, pero el paso 1 del guion la quiere en "Tranquilo". `SPEC.md` usaba `drift_threshold_pp` y el diseño, la fracción 0,10.
- Decisión: el campo se llama `drift_threshold`, es una **fracción** y vale 0,10 por defecto. 76 % frente a 70 % da Tranquilo; el ejemplo del producto (82 % frente a 70 %) sigue dando "Revisa tu plan". No se cambia ni el producto ni la cartera.
- Consecuencias: `SPEC.md` (§6, §8.5, §8.6, §13) y los contratos usan `drift_threshold`. Cierra Q3.
