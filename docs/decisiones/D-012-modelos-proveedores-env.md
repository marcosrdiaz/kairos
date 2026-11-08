### D-012 · Modelos y proveedores configurables por `.env`
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Decisión: `ANTHROPIC_MODEL_FAST` (def. `claude-haiku-5-5`), `ANTHROPIC_MODEL_DEEP` (def. `claude-sonnet-5-5`), IDs de ElevenLabs y proveedor de mercado en `.env`.
- Motivo: poder cambiar por coste o latencia sin tocar código; cierra la pregunta abierta "proveedor de LLM y voz" a falta de medir latencia.
