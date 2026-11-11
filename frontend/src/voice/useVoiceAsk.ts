/**
 * Flujo de una pregunta (UC-05): `pressStart` (al abrir el modo voz) → `WS /voice/stt` →
 * `pressEnd` → `POST /ask` (SSE) → cada frase aprobada se muestra y se encola su audio
 * (`/voice/tts`). Quien usa el hook decide cuándo termina el prompt de voz (en `VoiceMode`: tras
 * una pausa, sin voz o al llegar a `MAX_RECORDING_MS`).
 *
 * Plan B: si no hay micrófono o falla la transcripción, `problem` lo explica y la pantalla
 * ofrece el campo de texto (RF-15). Si falla el TTS, la respuesta se queda en texto
 * (`Turn.ttsFailed`).
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { streamAsk, type AskChannel } from "../api/ask";
import {
  STT_START,
  STT_STOP,
  fetchTts,
  mockTranscript,
  openStt,
  type SttServerMessage,
} from "../api/voice";
import { AudioQueue } from "./audioQueue";
import { MicrophoneDeniedError, startMicrophone, type Microphone } from "./microphone";
import { getSessionId } from "./session";

export type Phase = "idle" | "listening" | "transcribing" | "thinking" | "speaking";

export interface Sentence {
  index: number;
  text: string;
  calcIds: string[];
}

export interface Turn {
  /** Identificador local del turno (clave de React); el `turn_id` del backend no llega hasta `meta`. */
  id: number;
  question: string;
  channel: AskChannel;
  status: "idle" | "processing" | "complete" | "error";
  showDisclaimer: boolean;
  sentences: Sentence[];
  done: boolean;
  error: string | null;
  ttsFailed: boolean;
  /** El usuario cortó la lectura en voz alta (el texto se completa igual). */
  interrupted: boolean;
}

/**
 * Micrófono que ya estaba abierto (el que vigila si el usuario corta la respuesta) y que pasa
 * directamente a la transcripción, con lo último que grabó: así no se pierden las primeras
 * palabras de quien interrumpe.
 */
export interface MicHandoff {
  mic: Microphone;
  /** Audio PCM grabado justo antes de detectar la voz. */
  preroll: ArrayBuffer[];
  /** Redirige los trozos que siga grabando ese micrófono. */
  attach: (onChunk: (pcm: ArrayBuffer) => void) => void;
}

export interface Problem {
  /** `silence`: se escuchó y no se oyó a nadie (no se manda nada a transcribir). */
  kind: "mic" | "stt" | "silence";
  message: string;
}

/** Tope de un prompt de voz: al llegar, la pregunta se termina sola. */
export const MAX_RECORDING_MS = 45000;
const FINAL_TIMEOUT_MS = 12000;
const MOCK_TRANSCRIBE_MS = 600;
const MSG_MIC = "No puedo usar el micrófono. Puedes escribir tu pregunta.";
const MSG_STT = "No te he entendido. Prueba otra vez o escribe tu pregunta.";
const MSG_SILENCE = "No te he oído. Toca la esfera para seguir hablando.";
const MESSAGES: Record<Problem["kind"], string> = { mic: MSG_MIC, stt: MSG_STT, silence: MSG_SILENCE };
const MSG_ASK = "No puedo responder ahora mismo. Inténtalo de nuevo en unos minutos.";

interface SttSession {
  ws: WebSocket | null;
  mic: Microphone | null;
  ready: Promise<void>;
  finished: boolean;
  timer: number | undefined;
}

function waitOpen(ws: WebSocket): Promise<void> {
  return new Promise((resolve, reject) => {
    if (ws.readyState === WebSocket.OPEN) return resolve();
    ws.addEventListener("open", () => resolve(), { once: true });
    ws.addEventListener("error", () => reject(new Error("stt")), { once: true });
  });
}

/** Turnos que se conservan en pantalla (la conversación dura lo que la pestaña). */
const MAX_TURNS = 30;

/**
 * `speakAnswers`: si las respuestas se leen en voz alta (el interruptor de la pantalla). Vale
 * para las preguntas por voz y por texto; sin él, todo queda en texto.
 */
export function useVoiceAsk(portfolioId: string, speakAnswers: boolean) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [partial, setPartial] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const nextId = useRef(1);
  const activeTurnId = useRef<number | null>(null);
  const [problem, setProblem] = useState<Problem | null>(null);

  const stt = useRef<SttSession | null>(null);
  const abort = useRef<AbortController | null>(null);
  const streaming = useRef(false);
  const queue = useRef<AudioQueue | null>(null);
  /**
   * La lectura en voz alta de la respuesta en curso: si sigue activa, cómo cancelar sus audios
   * pendientes y cómo marcar el turno como interrumpido.
   */
  const voiced = useRef<{ on: boolean; tts: AbortController; markInterrupted: () => void } | null>(null);

  // Mientras se escucha al usuario, la cola de audio no cambia la fase.
  const getQueue = useCallback((): AudioQueue => {
    queue.current ??= new AudioQueue({
      onPlaying: () => !stt.current && setPhase("speaking"),
      onIdle: () => !stt.current && setPhase(streaming.current ? "thinking" : "idle"),
    });
    return queue.current;
  }, []);

  /**
   * Interrumpe la respuesta en curso: corta el audio, cancela los audios que aún se estaban
   * pidiendo y no lee lo que falta, pero el texto sigue llegando hasta completarse.
   */
  const interrupt = useCallback(() => {
    const voice = voiced.current;
    if (voice?.on && (queue.current?.busy || streaming.current)) voice.markInterrupted();
    if (voice) {
      voice.on = false;
      voice.tts.abort();
    }
    queue.current?.stop();
  }, []);

  const closeStt = useCallback(() => {
    const s = stt.current;
    stt.current = null;
    if (!s) return;
    s.finished = true;
    window.clearTimeout(s.timer);
    void s.mic?.stop();
    if (s.ws && s.ws.readyState <= WebSocket.OPEN) s.ws.close();
  }, []);

  const cancel = useCallback(() => {
    const turnId = activeTurnId.current;
    activeTurnId.current = null;
    if (turnId !== null) {
      setTurns((all) =>
        all.map((turn) => (turn.id === turnId ? { ...turn, status: "idle", done: true } : turn)),
      );
    }
    closeStt();
    abort.current?.abort();
    abort.current = null;
    streaming.current = false;
    queue.current?.stop();
    setPhase("idle");
  }, [closeStt]);

  useEffect(() => cancel, [cancel]);

  const ask = useCallback(
    async (question: string, channel: AskChannel) => {
      cancel();
      setProblem(null);
      const controller = new AbortController();
      abort.current = controller;
      streaming.current = true;
      const q = getQueue();
      const id = nextId.current++;
      const update = (patch: (t: Turn) => Partial<Turn>) =>
        setTurns((all) => all.map((t) => (t.id === id ? { ...t, ...patch(t) } : t)));
      const tts = new AbortController();
      controller.signal.addEventListener("abort", () => tts.abort(), { once: true });
      const voice = { on: speakAnswers, tts, markInterrupted: () => update(() => ({ interrupted: true })) };
      voiced.current = voice;
      const turn: Turn = {
        id,
        question,
        channel,
        status: "processing",
        showDisclaimer: false,
        sentences: [],
        done: false,
        error: null,
        ttsFailed: false,
        interrupted: false,
      };
      setTurns((all) => [...all, turn].slice(-MAX_TURNS));
      activeTurnId.current = id;
      setPhase("thinking");
      try {
        const request = { question, channel, session_id: getSessionId() };
        for await (const event of streamAsk(portfolioId, request, controller.signal)) {
          if (controller.signal.aborted) return;
          if (event.type === "meta" && event.disclaimer) {
            // El aviso de IA se muestra en texto, pero no se lee en voz alta (decisión del equipo).
            update(() => ({ showDisclaimer: true }));
          } else if (event.type === "sentence") {
            const sentence = { index: event.index, text: event.text, calcIds: event.calc_ids };
            update((t) => ({ sentences: [...t.sentences, sentence].sort((a, b) => a.index - b.index) }));
            if (voice.on) {
              const audio = fetchTts({ turn_id: event.turn_id, index: event.index }, tts.signal);
              q.enqueue(
                audio.then(
                  (blob) => (blob && voice.on ? URL.createObjectURL(blob) : null),
                  () => {
                    if (!tts.signal.aborted) update(() => ({ ttsFailed: true }));
                    return null;
                  },
                ),
              );
            }
          } else if (event.type === "done") {
            update(() => ({ done: true, status: "complete" }));
          } else if (event.type === "error") {
            update(() => ({ error: event.message, done: true, status: "error" }));
          }
        }
      } catch {
        if (controller.signal.aborted) {
          update(() => ({ done: true, status: "idle" }));
          return;
        }
        update(() => ({ error: MSG_ASK, done: true, status: "error" }));
      }
      update((t) => ({ done: true, status: t.status === "error" ? "error" : "complete" }));
      if (abort.current !== controller) return;
      streaming.current = false;
      activeTurnId.current = null;
      if (!q.busy && !stt.current) setPhase("idle");
    },
    [cancel, getQueue, portfolioId, speakAnswers],
  );

  const failStt = useCallback(
    (kind: Problem["kind"]) => {
      closeStt();
      setPartial("");
      setPhase(streaming.current ? "thinking" : "idle");
      setProblem({ kind, message: MESSAGES[kind] });
    },
    [closeStt],
  );

  const handleFinal = useCallback(
    (text: string | null) => {
      closeStt();
      setPartial("");
      if (!text?.trim()) return failStt("stt");
      void ask(text.trim(), "voice");
    },
    [ask, closeStt, failStt],
  );

  /**
   * Empieza a escuchar. La voz del usuario manda: si la respuesta anterior aún se está leyendo o
   * escribiendo, se corta su audio al momento (el texto se completa). Con `handoff`, se usa el
   * micrófono que ya estaba abierto y se manda primero lo que grabó justo antes.
   */
  const pressStart = useCallback((handoff?: MicHandoff) => {
    if (stt.current) {
      void handoff?.mic.stop();
      return;
    }
    interrupt();
    setProblem(null);
    setPartial("");
    setPhase("listening");
    const ws = openStt();
    const session: SttSession = {
      ws,
      mic: handoff?.mic ?? null, // el volumen de quien interrumpe se ve desde el primer momento
      ready: Promise.resolve(),
      finished: false,
      timer: undefined,
    };
    stt.current = session;
    if (!ws) {
      void handoff?.mic.stop(); // modo mock: se simula al terminar
      session.mic = null;
      return;
    }

    ws.onmessage = (event: MessageEvent<string>) => {
      const message = JSON.parse(event.data) as SttServerMessage;
      if (message.type === "partial") setPartial(message.text);
      else if (message.type === "final") handleFinal(message.text);
      else failStt("stt");
    };
    ws.onclose = () => {
      if (!session.finished && stt.current === session) failStt("stt");
    };
    // Micrófono y WebSocket arrancan a la vez; lo grabado antes de que abra el socket se
    // guarda y se manda después del `start`, para no perder la primera palabra.
    const pending: ArrayBuffer[] = [...(handoff?.preroll ?? [])];
    let open = false;
    const sink = (pcm: ArrayBuffer) => {
      if (open && ws.readyState === WebSocket.OPEN) ws.send(pcm);
      else pending.push(pcm);
    };
    let micReady: Promise<Microphone>;
    if (handoff) {
      handoff.attach(sink);
      micReady = Promise.resolve(handoff.mic);
    } else {
      micReady = startMicrophone(sink);
    }
    session.ready = (async () => {
      const [mic] = await Promise.all([micReady, waitOpen(ws)]);
      ws.send(JSON.stringify(STT_START));
      for (const pcm of pending.splice(0)) ws.send(pcm);
      open = true;
      if (session.finished) await mic.stop();
      else session.mic = mic;
    })();
    session.ready.catch(() => {
      void micReady.then((mic) => mic.stop(), () => undefined); // el socket falló: suelta el micro
    });
    session.ready.catch((err: unknown) => {
      if (stt.current === session) failStt(err instanceof MicrophoneDeniedError ? "mic" : "stt");
    });
  }, [failStt, handleFinal, interrupt]);

  const pressEnd = useCallback(async () => {
    const session = stt.current;
    if (!session || session.finished) return;
    setPhase("transcribing");
    if (!session.ws) {
      window.setTimeout(() => stt.current === session && handleFinal(mockTranscript()), MOCK_TRANSCRIBE_MS);
      return;
    }
    try {
      await session.ready;
    } catch {
      return; // ya se ha avisado
    }
    if (stt.current !== session) return;
    await session.mic?.stop();
    session.mic = null;
    if (session.ws.readyState === WebSocket.OPEN) session.ws.send(JSON.stringify(STT_STOP));
    session.timer = window.setTimeout(() => stt.current === session && failStt("stt"), FINAL_TIMEOUT_MS);
  }, [failStt, handleFinal]);

  /**
   * Volumen (0-1) para el visual de voz: el del micrófono mientras se escucha y el de la
   * respuesta mientras suena; 0 si no hay ninguno.
   */
  const getLevel = useCallback(
    () => stt.current?.mic?.level?.() ?? queue.current?.level() ?? 0,
    [],
  );

  /** Reinicia el chat: para lo que esté en marcha y borra la conversación de la pantalla. */
  const reset = useCallback(() => {
    cancel();
    setTurns([]);
    setProblem(null);
    setPartial("");
  }, [cancel]);

  /** Volumen (0-1) de la respuesta que está sonando (para distinguirla de la voz del usuario). */
  const playbackLevel = useCallback(() => queue.current?.level() ?? 0, []);

  /** Se dejó de escuchar sin oír a nadie: no se transcribe nada y se avisa. */
  const giveUp = useCallback(() => failStt("silence"), [failStt]);

  /**
   * Sale de la voz sin perder lo escrito: deja de escuchar y corta el audio, pero si una
   * respuesta se está escribiendo, termina de escribirse.
   */
  const endVoice = useCallback(() => {
    closeStt();
    interrupt();
    setPartial("");
    setProblem(null);
    setPhase(streaming.current ? "thinking" : "idle");
  }, [closeStt, interrupt]);

  return {
    phase,
    partial,
    turns,
    problem,
    pressStart,
    pressEnd,
    giveUp,
    endVoice,
    ask,
    cancel,
    reset,
    getLevel,
    playbackLevel,
  };
}
