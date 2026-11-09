import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { AskEvent, AskRequest } from "../api/ask";
import { VoiceAsk } from "./VoiceAsk";
import { MicrophoneDeniedError } from "./microphone";
import { AI_DISCLAIMER } from "./texts";

const TURN = "turn_test";
const askCalls: { portfolioId: string; request: AskRequest }[] = [];
let answer: AskEvent[] = [];
const tts = vi.fn(async () => new Blob(["mp3"], { type: "audio/mpeg" }));

/** WebSocket falso: abre en el siguiente tick y guarda lo que se le manda. */
class FakeSocket extends EventTarget {
  static last: FakeSocket | null = null;
  readyState = 0;
  sent: unknown[] = [];
  onmessage: ((e: MessageEvent<string>) => void) | null = null;
  onclose: (() => void) | null = null;
  constructor() {
    super();
    FakeSocket.last = this;
    setTimeout(() => {
      this.readyState = 1;
      this.dispatchEvent(new Event("open"));
    }, 0);
  }
  send(data: unknown) {
    this.sent.push(data);
  }
  close() {
    this.readyState = 3;
  }
  receive(message: object) {
    this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(message) }));
  }
}

vi.mock("../api/ask", () => ({
  streamAsk: async function* (portfolioId: string, request: AskRequest) {
    askCalls.push({ portfolioId, request });
    for (const event of answer) yield event;
  },
}));

vi.mock("../api/voice", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/voice")>()),
  openStt: () => new FakeSocket(),
  fetchTts: (...args: unknown[]) => tts(...(args as [])),
}));

const startMicrophone = vi.fn();
vi.mock("./microphone", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./microphone")>()),
  startMicrophone: (...args: unknown[]) => startMicrophone(...args),
}));

const flush = () => act(() => new Promise((r) => setTimeout(r, 10)));

beforeEach(() => {
  localStorage.clear();
  askCalls.length = 0;
  tts.mockClear();
  startMicrophone.mockReset();
  answer = [
    { type: "meta", turn_id: TURN, disclaimer: true },
    { type: "sentence", turn_id: TURN, index: 0, text: "Primera frase.", calc_ids: [] },
    { type: "sentence", turn_id: TURN, index: 1, text: "Segunda frase.", calc_ids: ["calc_1"] },
    { type: "done", turn_id: TURN, fallback_used: false, blocked_count: 0, first_sentence_ms: 500 },
  ];
  vi.spyOn(HTMLMediaElement.prototype, "play").mockImplementation(function (this: HTMLMediaElement) {
    setTimeout(() => this.dispatchEvent(new Event("ended")), 0);
    return Promise.resolve();
  });
  vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => undefined);
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:x");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("VoiceAsk", () => {
  it("una pregunta sugerida va por texto, muestra el aviso de IA y las frases, y las lee", async () => {
    render(<VoiceAsk portfolioId="laura" />);
    fireEvent.click(screen.getByRole("button", { name: "¿Por qué ha bajado?" }));
    await flush();
    expect(askCalls[0]?.portfolioId).toBe("laura");
    expect(askCalls[0]?.request.channel).toBe("text");
    expect(askCalls[0]?.request.session_id).toMatch(/^ses_/);
    expect(screen.getByText(AI_DISCLAIMER)).toBeTruthy();
    expect(screen.getByText("Primera frase.")).toBeTruthy();
    expect(screen.getByText("Segunda frase.").getAttribute("data-calc-ids")).toBe("calc_1");
    expect(tts).toHaveBeenCalledTimes(2);
  });

  it("con «leer en voz alta» apagado no pide audio, y la preferencia se recuerda", async () => {
    render(<VoiceAsk portfolioId="laura" />);
    const [toggle] = screen.getAllByRole("switch", { name: "Leer las respuestas en voz alta" });
    expect(toggle?.getAttribute("aria-checked")).toBe("true");
    fireEvent.click(toggle as HTMLElement);
    expect(localStorage.getItem("kairos.speak_answers")).toBe("false");
    fireEvent.change(screen.getByLabelText("Escribe tu pregunta"), { target: { value: "¿Voy bien?" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pregunta" }));
    await flush();
    expect(askCalls[0]?.request.question).toBe("¿Voy bien?");
    expect(tts).not.toHaveBeenCalled();
  });

  it("Intro envía la pregunta escrita y la conversación guarda el historial", async () => {
    render(<VoiceAsk portfolioId="laura" />);
    const input = screen.getByLabelText("Escribe tu pregunta");
    fireEvent.change(input, { target: { value: "Primera" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await flush();
    fireEvent.change(screen.getByLabelText("Escribe tu pregunta"), { target: { value: "Segunda" } });
    fireEvent.keyDown(screen.getByLabelText("Escribe tu pregunta"), { key: "Enter" });
    await flush();
    expect(askCalls.map((c) => c.request.question)).toEqual(["Primera", "Segunda"]);
    expect(screen.getByText("Primera")).toBeTruthy();
    expect(screen.getByText("Segunda")).toBeTruthy();
    expect(screen.getAllByText("Primera frase.")).toHaveLength(2);
  });

  it("si falla el TTS, la respuesta se queda en texto con una nota", async () => {
    tts.mockRejectedValue(new Error("503"));
    render(<VoiceAsk portfolioId="laura" />);
    fireEvent.click(screen.getByRole("button", { name: "¿Voy bien?" }));
    await flush();
    expect(screen.getByText("Primera frase.")).toBeTruthy();
    expect(screen.getByText(/No he podido leer esta respuesta en voz alta/)).toBeTruthy();
  });

  it("mantener pulsado transcribe y pregunta por voz", async () => {
    const mic = { stop: vi.fn(async () => undefined) };
    startMicrophone.mockResolvedValue(mic);
    render(<VoiceAsk portfolioId="javier" />);
    const button = screen.getByRole("button", { name: "Mantén pulsado para hablar" });
    fireEvent.keyDown(button, { key: " " });
    await flush();
    expect(screen.getByRole("status").textContent).toBe("Te escucho…");
    const ws = FakeSocket.last as FakeSocket;
    expect(JSON.parse(ws.sent[0] as string)).toMatchObject({ type: "start", sample_rate: 16000 });
    act(() => ws.receive({ type: "partial", text: "por qué" }));
    expect(screen.getByText("«por qué»")).toBeTruthy();
    fireEvent.keyUp(button, { key: " " });
    await flush();
    expect(mic.stop).toHaveBeenCalled();
    expect(JSON.parse(ws.sent.at(-1) as string)).toEqual({ type: "stop" });
    act(() => ws.receive({ type: "final", text: "¿Por qué ha bajado?" }));
    await flush();
    expect(askCalls[0]).toMatchObject({ portfolioId: "javier", request: { channel: "voice", question: "¿Por qué ha bajado?" } });
  });

  it("sin micrófono ofrece el plan B", async () => {
    startMicrophone.mockRejectedValue(new MicrophoneDeniedError("denegado"));
    render(<VoiceAsk portfolioId="laura" />);
    fireEvent.keyDown(screen.getByRole("button", { name: "Mantén pulsado para hablar" }), { key: "Enter" });
    await flush();
    expect(screen.getByRole("alert").textContent).toMatch(/No puedo usar el micrófono/);
    expect(screen.getByRole("button", { name: "¿Me afecta lo del BCE?" })).toBeTruthy();
  });

  it("si la transcripción falla, dice que no ha entendido", async () => {
    startMicrophone.mockResolvedValue({ stop: vi.fn(async () => undefined) });
    render(<VoiceAsk portfolioId="laura" />);
    fireEvent.keyDown(screen.getByRole("button", { name: "Mantén pulsado para hablar" }), { key: " " });
    await flush();
    act(() => FakeSocket.last?.receive({ type: "error", code: "UPSTREAM_UNAVAILABLE", message: "x" }));
    expect(screen.getByRole("alert").textContent).toMatch(/No te he entendido/);
    expect(askCalls).toHaveLength(0);
  });
});
