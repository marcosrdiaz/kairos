### D-010 · Guardián determinista, validación frase a frase
- Fecha: 2026-11-08 · Autor: P3 (propuesta inicial) · Estado: Propuesta
- Contexto: el guardián debe validar todo antes del usuario, pero la voz necesita streaming para < 2 s.
- Decisión: reglas deterministas (patrones prohibidos + comprobación de cifras) aplicadas a cada frase antes de mandarla al TTS. Bloqueo → reintento → plantilla. Verificación extra con LLM solo si `GUARDIAN_LLM_CHECK=true`.
- Alternativas descartadas: validar la respuesta entera antes de hablar (+0,5-1 s); solo LLM (lento y no determinista para tests).
- Consecuencias: si una frase intermedia se bloquea, se corta la respuesta y se completa con plantilla.
