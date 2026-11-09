### D-025 · Las magnitudes de un evento salen de los datos
- Fecha: 2026-11-08 · Autor: equipo · Estado: Sustituida por D-XXX (solo en lo de «el LLM elige canales»; las magnitudes siguen saliendo de `observed`)
- Contexto: decisión 11 del diseño; regla 1 de `CLAUDE.md`.
- Decisión: las magnitudes de los shocks salen del campo `observed` del JSON del replay. El LLM clasifica el evento, elige canales y redacta la cadena causal. `events` construye un `ShockSet` determinista; si el analizador falla, se usan todos los factores observados.
