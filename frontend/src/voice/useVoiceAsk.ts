/**
 * Flujo de una pregunta (UC-05): mantener pulsado → `WS /voice/stt` → `POST /ask` (SSE) →
 * cada frase aprobada se muestra y se encola su audio (`/voice/tts`).
 *
 * Plan B: si no hay micrófono o falla la transcripción, `problem` lo explica y la pantalla
 * ofrece las preguntas sugeridas y el campo de texto (RF-15). Si falla el TTS, la respuesta
 * se queda en texto (`Turn.ttsFailed`).
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { streamAsk, type AskChannel } from "../api/ask";
import {
  DISCLAIMER_URL,
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
  showDisclaimer: boolean;
  sentences: Sentence[];
  done: boolean;
  error: string | null;
  ttsFailed: boolean;
}

export interface Problem {
  kind: "mic" | "stt";
  message: string;
}

const FINAL_TIMEOUT_MS = 12000;
const MOCK_TRANSCRIBE_MS = 600;
const MSG_MIC = "No puedo usar el micrófono. Puedes escribir tu pregunta o elegir una de estas.";
const MSG_STT = "No te he entendido. Prueba otra vez o elige una de estas preguntas.";
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
  const [problem, setProblem] = useState<Problem | null>(null);

  const stt = useRef<SttSession | null>(null);
  const abort = useRef<AbortController | null>(null);
  const streaming = useRef(false);
  const queue = useRef<AudioQueue | null>(null);

  const getQueue = useCallback((): AudioQueue => {
    queue.current ??= new AudioQueue({
      onPlaying: () => setPhase("speaking"),
      onIdle: () => setPhase(streaming.current ? "thinking" : "idle"),
    });
    return queue.current;
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
      const speak = speakAnswers;
      const q = getQueue();
      const id = nextId.current++;
      const update = (patch: (t: Turn) => Partial<Turn>) =>
        setTurns((all) => all.map((t) => (t.id === id ? { ...t, ...patch(t) } : t)));
      const turn: Turn = {
        id,
        question,
        channel,
        showDisclaimer: false,
        sentences: [],
        done: false,
        error: null,
        ttsFailed: false,
      };
      setTurns((all) => [...all, turn].slice(-MAX_TURNS));
      setPhase("thinking");
      try {
        const request = { question, channel, session_id: getSessionId() };
        for await (const event of streamAsk(portfolioId, request, controller.signal)) {
          if (event.type === "meta" && event.disclaimer) {
            update(() => ({ showDisclaimer: true }));
            if (speak) q.enqueue(Promise.resolve(DISCLAIMER_URL), false);
          } else if (event.type === "sentence") {
            const sentence = { index: event.index, text: event.text, calcIds: event.calc_ids };
            update((t) => ({ sentences: [...t.sentences, sentence].sort((a, b) => a.index - b.index) }));
            if (speak) {
              const audio = fetchTts({ turn_id: event.turn_id, index: event.index }, controller.signal);
              q.enqueue(
                audio.then(
                  (blob) => (blob ? URL.createObjectURL(blob) : null),
                  () => {
                    if (!controller.signal.aborted) update(() => ({ ttsFailed: true }));
                    return null;
                  },
                ),
              );
            }
          } else if (event.type === "done") {
            update(() => ({ done: true }));
          } else if (event.type === "error") {
            update(() => ({ error: event.message, done: true }));
          }
        }
      } catch {
        update(() => (controller.signal.aborted ? { done: true } : { error: MSG_ASK, done: true }));
        if (controller.signal.aborted) return;
      }
      update(() => ({ done: true })); // también si se paró a medias
      if (abort.current !== controller) return;
      streaming.current = false;
      if (!q.busy) setPhase("idle");
    },
    [cancel, getQueue, portfolioId, speakAnswers],
  );

  const failStt = useCallback(
    (kind: Problem["kind"]) => {
      closeStt();
      setPartial("");
      setPhase("idle");
      setProblem({ kind, message: kind === "mic" ? MSG_MIC : MSG_STT });
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

  const pressStart = useCallback(() => {
    if (stt.current) return;
    cancel();
    setProblem(null);
    setPartial("");
    setPhase("listening");
    const ws = openStt();
    const session: SttSession = { ws, mic: null, ready: Promise.resolve(), finished: false, timer: undefined };
    stt.current = session;
    if (!ws) return; // modo mock: se simula al soltar

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
    const pending: ArrayBuffer[] = [];
    let open = false;
    const micReady = startMicrophone((pcm) => {
      if (open && ws.readyState === WebSocket.OPEN) ws.send(pcm);
      else pending.push(pcm);
    });
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
  }, [cancel, failStt, handleFinal]);

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

  return { phase, partial, turns, problem, pressStart, pressEnd, ask, cancel };
}
