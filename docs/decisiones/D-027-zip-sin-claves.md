### D-027 · El ZIP sin claves de Claude y ElevenLabs
- Fecha: 2026-11-08 · Autor: equipo · Estado: Aceptada
- Contexto: decisión 13 del diseño.
- Decisión: las claves son necesarias para la IA (el README las pide en `.env.example`). Sin claves la app arranca: el explicador responde con plantillas construidas con datos del motor (`fallback_used: true`) y no hay audio. No hay respuestas pregrabadas.
