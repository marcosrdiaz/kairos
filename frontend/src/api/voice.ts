/**
 * Voz (diseño del MVP §4.5): `WS /voice/stt`, `POST /voice/tts` y `GET /voice/disclaimer`.
 *
 * FastAPI no documenta el WebSocket, así que sus mensajes se tipan aquí a partir de los
 * ejemplos `Stt*Message` de `mocks/` (D-040). El TTS solo lee frases ya aprobadas por el
 * guardián: se pide por `turn_id` e `index`, nunca con texto.
 *
 * Con VITE_USE_MOCKS=true no hay audio ni WebSocket: `openStt` devuelve `null` y quien la usa
 * simula la transcripción con `mockTranscript()`; `fetchTts` devuelve `null` (solo texto).
 */
import { getMock, toApiError } from "./client";
import type { TtsRequest } from "./generated/schema";

const BASE = "/api/v1";
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";

export const STT_SAMPLE_RATE = 16000;

export interface SttStartMessage {
  type: "start";
  sample_rate: typeof STT_SAMPLE_RATE;
  encoding: "pcm_s16le";
  language: "es";
}

export interface SttStopMessage {
  type: "stop";
}

export interface SttPartialMessage {
  type: "partial";
  text: string;
}

export interface SttFinalMessage {
  type: "final";
  text: string;
}

export interface SttErrorMessage {
  type: "error";
  code: string;
  message: string;
}

export type SttServerMessage = SttPartialMessage | SttFinalMessage | SttErrorMessage;

export const STT_START: SttStartMessage = {
  type: "start",
  sample_rate: STT_SAMPLE_RATE,
  encoding: "pcm_s16le",
  language: "es",
};

export const STT_STOP: SttStopMessage = { type: "stop" };

/** URL del audio pregenerado del aviso de IA. */
export const DISCLAIMER_URL = `${BASE}/voice/disclaimer`;

/** Abre el WebSocket de transcripción (mismo origen: Vite lo reenvía al backend). */
export function openStt(): WebSocket | null {
  if (USE_MOCKS) return null;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${protocol}//${window.location.host}${BASE}/voice/stt`);
  ws.binaryType = "arraybuffer";
  return ws;
}

/** Transcripción de ejemplo para el modo mock (la de `SttFinalMessage.json`). */
export function mockTranscript(): string | null {
  return getMock<SttFinalMessage>("SttFinalMessage")?.text ?? null;
}

/**
 * MP3 de una frase aprobada. Lanza `ApiError` si no está aprobada (404) o si ElevenLabs falla
 * (503); quien la usa deja la respuesta en texto.
 */
export async function fetchTts(request: TtsRequest, signal?: AbortSignal): Promise<Blob | null> {
  if (USE_MOCKS) return null;
  const path = "/voice/tts";
  const init: RequestInit = {
    method: "POST",
    headers: { Accept: "audio/mpeg", "Content-Type": "application/json" },
    body: JSON.stringify(request),
  };
  if (signal) init.signal = signal;
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) throw await toApiError("POST", path, res);
  return await res.blob();
}
