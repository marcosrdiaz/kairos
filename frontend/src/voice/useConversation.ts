/**
 * Modo conversación: hablar con KAIROS como en una llamada, sin pulsar nada entre turnos. La voz
 * del usuario tiene prioridad sobre la de la respuesta.
 *
 * - Al terminar cada respuesta (cuando acaba de sonar o, sin voz, de escribirse), vuelve a
 *   escuchar solo.
 * - Se le puede cortar hablando. Mientras prepara o lee la respuesta hay un micrófono abierto
 *   que mide el volumen y guarda lo último que oye (`BARGE_IN.prerollMs`), sin mandar nada. El
 *   detector (`bargeIn.ts`) aprende cuánto de la respuesta se cuela por el micrófono y corta solo
 *   cuando la voz del usuario lo supera. Entonces ese mismo micrófono pasa a la transcripción con
 *   lo que acaba de grabar (no se pierden las primeras palabras); el audio de la respuesta se
 *   corta al momento y su texto se termina de escribir. (Tocar la esfera también corta.)
 * - Si hay un problema (no se oyó nada, no se entendió), se queda en pausa: no vuelve a escuchar
 *   hasta que se toca la esfera.
 *
 * Diagnóstico: con `localStorage.setItem("kairos.voiceDebug", "1")`, la consola muestra cada
 * 200 ms el volumen del micrófono, el de la respuesta y el umbral.
 */
import { useEffect, useRef } from "react";
import { BARGE_IN, BargeDetector } from "./bargeIn";
import { startMicrophone, type Microphone } from "./microphone";
import type { MicHandoff, Phase, Problem } from "./useVoiceAsk";

const CHECK_EVERY_MS = 40;
const CHUNK_MS = 100; // el micrófono manda trozos de 100 ms (microphone.ts)
const DEBUG_EVERY_MS = 200;

function debugEnabled(): boolean {
  try {
    return localStorage.getItem("kairos.voiceDebug") === "1";
  } catch {
    return false;
  }
}

interface ConversationOptions {
  active: boolean;
  phase: Phase;
  problem: Problem | null;
  listen: (handoff?: MicHandoff) => void;
  /** Volumen (0-1) de la respuesta que está sonando. */
  playbackLevel: () => number;
}

export function useConversation({ active, phase, problem, listen, playbackLevel }: ConversationOptions): void {
  const previous = useRef<Phase>(phase);
  const listenRef = useRef(listen);
  const playbackRef = useRef(playbackLevel);
  useEffect(() => {
    listenRef.current = listen;
    playbackRef.current = playbackLevel;
  });

  // Fin de una respuesta → vuelve a escuchar.
  useEffect(() => {
    const was = previous.current;
    previous.current = phase;
    const answered = was === "thinking" || was === "speaking";
    if (active && !problem && phase === "idle" && answered) listenRef.current();
  }, [active, phase, problem]);

  // Mientras responde: micrófono vigilando para que el usuario pueda cortar hablando.
  const answering = active && (phase === "thinking" || phase === "speaking");
  useEffect(() => {
    if (!answering) return;
    let stopped = false;
    let handedOff = false;
    let mic: Microphone | null = null;
    let timer: number | undefined;
    const preroll: ArrayBuffer[] = [];
    const keep = Math.ceil(BARGE_IN.prerollMs / CHUNK_MS);
    let sink = (pcm: ArrayBuffer) => {
      preroll.push(pcm);
      if (preroll.length > keep) preroll.shift();
    };
    const debug = debugEnabled();

    startMicrophone((pcm) => sink(pcm)).then(
      (m) => {
        if (stopped) {
          void m.stop();
          return;
        }
        mic = m;
        const detector = new BargeDetector();
        let lastLog = 0;
        timer = window.setInterval(() => {
          const now = Date.now();
          const barge = detector.update(m.level?.() ?? 0, playbackRef.current(), now);
          if (debug && now - lastLog >= DEBUG_EVERY_MS) {
            lastLog = now;
            const { mic: l, playback, threshold } = detector.last;
            console.debug(`[voz] micro ${l.toFixed(2)} · respuesta ${playback.toFixed(2)} · umbral ${threshold.toFixed(2)}`);
          }
          if (!barge) return;
          if (debug) console.debug("[voz] corte por voz");
          window.clearInterval(timer);
          handedOff = true;
          listenRef.current({
            mic: m,
            preroll: preroll.splice(0),
            attach: (onChunk) => {
              sink = onChunk;
            },
          });
        }, CHECK_EVERY_MS);
      },
      () => undefined, // sin micrófono no hay corte por voz; tocar la esfera sigue cortando
    );
    return () => {
      stopped = true;
      window.clearInterval(timer);
      if (!handedOff) void mic?.stop();
    };
  }, [answering]);
}
