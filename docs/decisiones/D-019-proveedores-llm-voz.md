### D-019 · Proveedor de LLM y voz
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 4 del diseño del MVP.
- Decisión: Claude (Haiku 5.5 rápido y Sonnet 5.5 profundo, por `.env`) + ElevenLabs (Scribe v2 Realtime y Flash v2.5). Si la medición de latencia (T2-16) falla, se cambia de modelo o de voz, no de proveedor. Confirma D-012.
- Consecuencias: T0-09 verifica los IDs exactos.
