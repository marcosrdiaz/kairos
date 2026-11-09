/**
 * `POST /portfolios/{id}/ask` (diseño del MVP §4.4): respuesta `text/event-stream`, una línea
 * `data: {...}` por evento. FastAPI no documenta el SSE en el OpenAPI, así que los eventos se
 * tipan aquí a partir de `backend/app/schemas/agents.py` (y de sus ejemplos en `mocks/`).
 *
 * Con VITE_USE_MOCKS=true emite los ejemplos de `mocks/` (meta, dos frases y done).
 */
import { getMock, toApiError } from "./client";
import type { AskRequest } from "./generated/schema";

export type { AskChannel, AskRequest } from "./generated/schema";

export interface AskMetaEvent {
  type: "meta";
  turn_id: string;
  disclaimer: boolean;
}

export interface AskSentenceEvent {
  type: "sentence";
  turn_id: string;
  index: number;
  text: string;
  calc_ids: string[];
}

export interface AskDoneEvent {
  type: "done";
  turn_id: string;
  fallback_used: boolean;
  blocked_count: number;
  first_sentence_ms: number;
}

export interface AskErrorEvent {
  type: "error";
  turn_id: string;
  code: string;
  message: string;
}

export type AskEvent = AskMetaEvent | AskSentenceEvent | AskDoneEvent | AskErrorEvent;

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";
const MOCK_EVENTS = ["AskMetaEvent", "AskSentenceEvent", "AskSentenceEvent.impact", "AskDoneEvent"];
const MOCK_DELAY_MS = 400;

/**
 * Separa un buffer SSE en eventos completos. Devuelve los eventos y el resto sin terminar
 * (que se concatena con el siguiente trozo de la respuesta).
 */
export function parseSse(buffer: string): { events: AskEvent[]; rest: string } {
  const normalized = buffer.replace(/\r\n/g, "\n");
  const blocks = normalized.split("\n\n");
  const rest = blocks.pop() ?? "";
  const events: AskEvent[] = [];
  for (const block of blocks) {
    const data = block
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart())
      .join("\n");
    if (data) events.push(JSON.parse(data) as AskEvent);
  }
  return { events, rest };
}

async function* mockAsk(signal?: AbortSignal): AsyncGenerator<AskEvent> {
  for (const name of MOCK_EVENTS) {
    await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY_MS));
    if (signal?.aborted) return;
    const event = getMock<AskEvent>(name);
    if (event) yield event;
  }
}

/** Eventos de la respuesta, en orden. Un 4xx/5xx antes del stream sale como `ApiError`. */
export async function* streamAsk(
  portfolioId: string,
  request: AskRequest,
  signal?: AbortSignal,
): AsyncGenerator<AskEvent> {
  if (USE_MOCKS) {
    yield* mockAsk(signal);
    return;
  }
  const path = `/portfolios/${encodeURIComponent(portfolioId)}/ask`;
  const init: RequestInit = {
    method: "POST",
    headers: { Accept: "text/event-stream", "Content-Type": "application/json" },
    body: JSON.stringify(request),
  };
  if (signal) init.signal = signal;
  const res = await fetch(`/api/v1${path}`, init);
  if (!res.ok || !res.body) throw await toApiError("POST", path, res);
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      const parsed = parseSse(buffer + value);
      buffer = parsed.rest;
      yield* parsed.events;
    }
    yield* parseSse(`${buffer}\n\n`).events;
  } finally {
    reader.releaseLock();
  }
}
