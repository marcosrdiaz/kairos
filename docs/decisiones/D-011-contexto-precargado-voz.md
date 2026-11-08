### D-011 · Contexto precargado para la voz
- Fecha: 2026-11-08 · Autor: P3 (propuesta inicial) · Estado: Propuesta
- Contexto: cada ronda de tool calling añade ~0,5-1 s.
- Decisión: el prompt del explicador incluye un bloque de contexto con caché (patrimonio, asignación, eventos de 7 días con impacto, estado del plan); las herramientas solo se usan para preguntas fuera de ese contexto.
- Consecuencias: el guardián acepta cifras del bloque de contexto como fuente válida.
