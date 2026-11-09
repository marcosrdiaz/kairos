### D-XXX · Latencia de voz (T2-16): 9/10 por debajo de 2 s con una primera frase corta en el prompt del explicador; sin cambiar de modelo ni de voz
- Fecha: 2026-11-09 · Autor: Javi · Estado: Propuesta
- Contexto: RF-14 pide la primera palabra de la respuesta hablada en menos de 2 s, y el criterio de T2-16 es 8 de 10 intentos por debajo. La decisión 4 (D-019) dice que, si no se cumple, se cambia de modelo o de voz, no de proveedor. El presupuesto del diseño (§2), contado desde que se suelta el botón, era: STT ~300 ms + primera frase de Claude ~700–900 ms + guardián < 20 ms + TTS ~300 ms ≈ 1,5 s.
- Cómo se mide: `scripts/measure_voice.py` contra un backend corriendo, con ElevenLabs y Claude (`claude-haiku-5-5`) reales y desde una conexión doméstica. Hace lo mismo que el frontend (T2-14): manda el audio PCM de la pregunta a ritmo real por `WS /voice/stt` y, desde el `stop`, cronometra el `final`, después `POST /ask` hasta la primera `sentence` y después `POST /voice/tts` hasta el primer byte. No cuenta el aviso de IA, que suena antes y tapa la espera: es el caso peor. Con `--prepare` deja el estado del guion (`/demo/reset` con `preload` y el replay de NVIDIA). Antes de medir calienta la caché del prompt de las dos carteras. Rota las 3 preguntas tipo (dos de Laura y una de Javier).
- Resultados (10 intentos cada uno):

  | Configuración | Bajo 2 s | Total (mediana / máx.) | STT | 1.ª frase de `/ask` | TTS 1.er byte |
  | --- | --- | --- | --- | --- | --- |
  | Prompt actual, sin eventos cargados (no es el estado del guion) | 3/10 | 2.723 / 3.832 ms | 171 ms | 2.344 ms | 221 ms |
  | Prompt actual, estado del guion | 5/10 | 1.949 / 3.514 ms | 182 ms | 1.566 ms | 219 ms |
  | **Prompt con primera frase corta, estado del guion** | **9/10** | **1.707 / 2.088 ms** | 161 ms | 1.295 ms | 230 ms |

  (STT, primera frase y TTS en mediana.)
- Diagnóstico:
  - **La voz cumple de sobra.** El STT `final` llega en ~160–180 ms tras soltar y el primer byte del TTS en ~220 ms. Cambiar de modelo o de voz de ElevenLabs no ganaría nada.
  - **El cuello de botella es la primera frase completa de Claude.** El guardián necesita la frase entera, y con el prompt actual las primeras frases tienen 25–30 palabras: ~1,5 s de mediana aun con el prompt en caché (~9.200 tokens leídos de caché) y sin herramientas. Haiku 5.5 ya es el modelo más rápido, así que cambiar de modelo tampoco ayuda.
  - **«BCE» llega a veces transcrito como «BC».** Claude contesta entonces comentando la pregunta («The question is ambiguous…»), el guardián lo bloquea y el reintento suma ~1,5 s.
  - Picos que quedan: cuando Claude decide usar una herramienta (una ida y vuelta más, ~1,3 s) y cuando la caché del prompt se recrea.
- Decisión:
  - **No se cambia de modelo ni de voz** (decisión 4): no son el cuello de botella.
  - Se añaden dos reglas a `backend/app/agents/prompts/explainer.md`, en «La respuesta»: (1) la primera frase es corta, de como mucho 12 palabras, con la cifra y la idea principal, y los detalles van en las siguientes; (2) la pregunta puede venir de un dictado por voz con errores («BC» por «BCE»): se entiende por el contexto y se responde en español sin comentar la pregunta. Con ellas, 9/10.
  - **Antes de la demo se calienta la caché del prompt de las dos carteras**: una pregunta a Laura y otra a Javier tras el `/demo/reset`. Sin eso, la primera pregunta de cada cartera paga la creación de la caché (+1–3 s).
- Motivo: es el cambio más pequeño que cumple el criterio, y una primera frase corta con la cifra también es mejor respuesta hablada (RF-14: «al menos una cifra en €»).
- Alternativas descartadas: otro modelo de Claude (Haiku ya es el más rápido); otra voz o modelo de ElevenLabs (STT y TTS suman ~400 ms); trocear la primera frase por comas para el TTS (el guardián valida frases completas, regla 3).
- Consecuencias:
  - Fichero fuera de la fila de T2-16: `backend/app/agents/prompts/explainer.md` (de T1-17, ya hecha), con aviso a Manu en el tablero.
  - Pendientes para quien coja T2-09: el contexto precargado de Laura cambia de tamaño entre turnos sin que cambie el estado (9.213 → 9.250 tokens de caché en la misma sesión), y eso fuerza a recrear la caché del prompt. Y en «¿Por qué ha bajado?» Claude a veces suma cifras por su cuenta («320 euros»): el guardián lo bloquea (bien), pero acaba en plantilla y tarda más.
  - La medición se repite con `cd backend && uv run python ../scripts/measure_voice.py --prepare`, que sale con código 1 si no se llega a 8/10.
