import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { AskEvent, AskRequest } from "../api/ask";
import { VoiceAsk } from "./VoiceAsk";
import { MicrophoneDeniedError } from "./microphone";
import { AI_DISCLAIMER } from "./texts";

const TURN = "turn_test";
const askCalls: { portfolioId: string; request: AskRequest }[] = [];
let answer: AskEvent[] = [];
let streamGate: Promise<void> | null = null;
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
    for (const [i, event] of answer.entries()) {
      if (i === 2 && streamGate) await streamGate;
      yield event;
    }
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

function typeAndSend(question: string) {
  fireEvent.change(screen.getByLabelText("Escribe tu pregunta"), { target: { value: question } });
  fireEvent.click(screen.getByRole("button", { name: "Enviar pregunta" }));
}

/** Una frase de la respuesta (se escribe palabra a palabra, así que va en varios nodos). */
const sentence = (text: string) =>
  screen.getByText((_, el) => !!el?.classList.contains("chat-line") && el.textContent === text);
const sentences = (text: string) =>
  screen.queryAllByText((_, el) => !!el?.classList.contains("chat-line") && el.textContent === text);

/** La esfera: activa el modo conversación. */
const openVoice = () => fireEvent.click(screen.getByRole("button", { name: "Empezar a hablar con Kairos" }));

const flush = () => act(() => new Promise((r) => setTimeout(r, 10)));

beforeEach(() => {
  localStorage.clear();
  askCalls.length = 0;
  streamGate = null;
  tts.mockReset();
  tts.mockImplementation(async () => new Blob(["mp3"], { type: "audio/mpeg" }));
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
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("VoiceAsk", () => {
  it("una pregunta escrita va por texto, muestra el aviso de IA y las frases seguidas, y las lee", async () => {
    render(<VoiceAsk portfolioId="laura" />);
    expect(screen.queryByText("Respuesta en curso")).toBeNull();
    typeAndSend("¿Por qué ha bajado?");
    await flush();
    expect(askCalls[0]?.portfolioId).toBe("laura");
    expect(askCalls[0]?.request.channel).toBe("text");
    expect(askCalls[0]?.request.session_id).toMatch(/^ses_/);
    expect(screen.getByText(AI_DISCLAIMER)).toBeTruthy();
    expect(sentence("Primera frase.")).toBeTruthy();
    expect(sentence("Segunda frase.").getAttribute("data-calc-ids")).toBe("calc_1");
    // Las frases van en el mismo párrafo, no en uno cada una.
    expect(sentence("Primera frase.").parentElement).toBe(sentence("Segunda frase.").parentElement);
    expect(tts).toHaveBeenCalledTimes(2);
  });

  it("mantiene el estado en curso hasta que termina el stream y después lo marca como listo", async () => {
    let release!: () => void;
    streamGate = new Promise<void>((resolve) => (release = resolve));
    render(<VoiceAsk portfolioId="laura" />);
    typeAndSend("¿Voy bien?");
    await waitFor(() => expect(screen.getByText("Respuesta en curso")).toBeTruthy());
    expect(screen.queryByText("Respuesta lista")).toBeNull();

    release();
    await waitFor(() => expect(screen.getByText("Respuesta lista")).toBeTruthy());
    expect(screen.queryByText("Respuesta en curso")).toBeNull();
  });

  it("marca como error una respuesta rechazada por el stream", async () => {
    answer = [
      { type: "error", turn_id: TURN, code: "UPSTREAM_UNAVAILABLE", message: "No puedo responder." },
    ];
    render(<VoiceAsk portfolioId="laura" />);
    typeAndSend("¿Voy bien?");
    await waitFor(() => expect(screen.getByText("No se pudo completar")).toBeTruthy());
    expect(screen.getByRole("alert").textContent).toContain("No puedo responder.");
    expect(screen.queryByText("Respuesta lista")).toBeNull();
  });

  it("una respuesta cancelada no aparece como completada", async () => {
    let release!: () => void;
    streamGate = new Promise<void>((resolve) => (release = resolve));
    render(<VoiceAsk portfolioId="laura" />);
    typeAndSend("¿Voy bien?");
    await waitFor(() => expect(screen.getByText("Respuesta en curso")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Parar" }));
    expect(screen.queryByText("Respuesta en curso")).toBeNull();
    expect(screen.queryByText("Respuesta lista")).toBeNull();

    release();
    await flush();
    expect(screen.queryByText("Respuesta lista")).toBeNull();
  });

  it("con «leer en voz alta» apagado no pide audio, y la preferencia se recuerda", async () => {
    render(<VoiceAsk portfolioId="laura" />);
    const toggle = screen.getByRole("switch", { name: "Leer las respuestas en voz alta" });
    expect(toggle.getAttribute("aria-checked")).toBe("true");
    fireEvent.click(toggle);
    expect(localStorage.getItem("kairos.speak_answers")).toBe("false");
    fireEvent.change(screen.getByLabelText("Escribe tu pregunta"), { target: { value: "¿Voy bien?" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar pregunta" }));
    await flush();
    expect(askCalls[0]?.request.question).toBe("¿Voy bien?");
    expect(tts).not.toHaveBeenCalled();
  });

  it("Intro envía la pregunta escrita y la conversación guarda el historial", async () => {
    render(<VoiceAsk portfolioId="laura" />);
    expect((screen.getByRole("button", { name: "Enviar pregunta" }) as HTMLButtonElement).disabled).toBe(true);
    const input = screen.getByLabelText("Escribe tu pregunta");
    fireEvent.change(input, { target: { value: "Pregunta A" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await flush();
    fireEvent.change(screen.getByLabelText("Escribe tu pregunta"), { target: { value: "Pregunta B" } });
    fireEvent.keyDown(screen.getByLabelText("Escribe tu pregunta"), { key: "Enter" });
    await flush();
    expect(askCalls.map((c) => c.request.question)).toEqual(["Pregunta A", "Pregunta B"]);
    expect(screen.getByText("Pregunta A")).toBeTruthy();
    expect(screen.getByText("Pregunta B")).toBeTruthy();
    expect(sentences("Primera frase.")).toHaveLength(2);
  });

  it("si falla el TTS, la respuesta se queda en texto con una nota", async () => {
    tts.mockRejectedValue(new Error("503"));
    render(<VoiceAsk portfolioId="laura" />);
    typeAndSend("¿Voy bien?");
    await flush();
    expect(sentence("Primera frase.")).toBeTruthy();
    expect(screen.getByText(/No he podido leer esta respuesta en voz alta/)).toBeTruthy();
  });

  it("la esfera activa la conversación: escucha, tras 2 s de silencio pregunta y vuelve a escuchar", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let speaking = true;
    const mic = { stop: vi.fn(async () => undefined), level: () => (speaking ? 0.6 : 0.01) };
    startMicrophone.mockResolvedValue(mic);
    render(<VoiceAsk portfolioId="javier" />);
    openVoice();
    // En conversación la esfera no es un botón, hay «Terminar la conversación» y no hay barra de texto.
    expect(screen.queryByRole("button", { name: "Empezar a hablar con Kairos" })).toBeNull();
    expect(screen.getByRole("button", { name: "Terminar la conversación" })).toBeTruthy();
    expect(screen.getByLabelText("Escribe tu pregunta").closest("[inert]")).not.toBeNull();
    await flush();
    expect(startMicrophone).toHaveBeenCalled();
    expect(screen.getByRole("status").textContent).toBe("Te escucho…");
    const ws = FakeSocket.last as FakeSocket;
    expect(JSON.parse(ws.sent[0] as string)).toMatchObject({ type: "start", sample_rate: 16000 });
    act(() => ws.receive({ type: "partial", text: "por qué" }));
    expect(screen.getByText("por qué")).toBeTruthy();

    await act(async () => vi.advanceTimersByTimeAsync(500)); // habla
    speaking = false;
    await act(async () => vi.advanceTimersByTimeAsync(1500)); // pausa corta: sigue escuchando
    expect(mic.stop).not.toHaveBeenCalled();
    await act(async () => vi.advanceTimersByTimeAsync(800)); // > 2 s de silencio
    await flush();
    expect(mic.stop).toHaveBeenCalled();
    expect(JSON.parse(ws.sent.at(-1) as string)).toEqual({ type: "stop" });
    // Reloj real antes de la respuesta: el audio falso termina con un setTimeout que, con el reloj
    // simulado, no llegaría a dispararse.
    vi.useRealTimers();
    act(() => ws.receive({ type: "final", text: "¿Por qué ha bajado?" }));
    await flush();
    expect(askCalls[0]).toMatchObject({ portfolioId: "javier", request: { channel: "voice", question: "¿Por qué ha bajado?" } });
    expect(sentence("Primera frase.")).toBeTruthy();
    // Terminada la respuesta (suenan las dos frases), vuelve a escuchar sin pulsar nada.
    await waitFor(() => expect(screen.getByRole("status").textContent).toBe("Te escucho…"));
  });

  it("«Terminar la conversación» sale del modo voz sin preguntar y vuelve la barra de texto", () => {
    startMicrophone.mockResolvedValue({ stop: vi.fn(async () => undefined) });
    render(<VoiceAsk portfolioId="laura" />);
    openVoice();
    fireEvent.click(screen.getByRole("button", { name: "Terminar la conversación" }));
    expect(screen.queryByRole("button", { name: "Terminar la conversación" })).toBeNull();
    expect(screen.getByLabelText("Escribe tu pregunta").closest("[inert]")).toBeNull();
    expect(screen.getByRole("button", { name: "Empezar a hablar con Kairos" })).toBeTruthy();
    expect(askCalls).toHaveLength(0);
  });

  it("interrumpir mientras lee en voz alta corta el audio, termina el texto y escucha", async () => {
    let release!: () => void;
    const gate = new Promise<void>((r) => (release = r));
    const pause = HTMLMediaElement.prototype.pause as unknown as ReturnType<typeof vi.fn>;
    // El primer audio "suena" sin terminar, para poder interrumpirlo.
    vi.mocked(HTMLMediaElement.prototype.play).mockImplementation(() => Promise.resolve());
    answer = [
      { type: "meta", turn_id: TURN, disclaimer: false },
      { type: "sentence", turn_id: TURN, index: 0, text: "Primera frase.", calc_ids: [] },
      { type: "sentence", turn_id: TURN, index: 1, text: "Segunda frase.", calc_ids: [] },
      { type: "done", turn_id: TURN, fallback_used: false, blocked_count: 0, first_sentence_ms: 500 },
    ];
    streamGate = gate;
    startMicrophone.mockResolvedValue({ stop: vi.fn(async () => undefined) });
    render(<VoiceAsk portfolioId="laura" />);
    typeAndSend("¿Voy bien?");
    await flush();
    await waitFor(() => expect(screen.getByRole("status").textContent).toBe("Respondiendo en voz alta…"));
    openVoice();
    await flush();
    expect(pause).toHaveBeenCalled();
    expect(screen.getByRole("status").textContent).toBe("Te escucho…");
    release();
    await flush();
    expect(sentence("Segunda frase.")).toBeTruthy();
    expect(tts).toHaveBeenCalledTimes(1); // lo que faltaba ya no se lee
    expect(screen.getByRole("status").textContent).toBe("Te escucho…");
  });

  it("en conversación, la voz del usuario manda: cortar hablando para el audio y pasa su voz al STT", async () => {
    vi.mocked(HTMLMediaElement.prototype.play).mockImplementation(() => Promise.resolve()); // no termina
    const pause = HTMLMediaElement.prototype.pause as unknown as ReturnType<typeof vi.fn>;
    let level = 0;
    const sinks: ((pcm: ArrayBuffer) => void)[] = [];
    const mics: { stop: ReturnType<typeof vi.fn> }[] = [];
    startMicrophone.mockImplementation(async (onChunk: (pcm: ArrayBuffer) => void) => {
      sinks.push(onChunk);
      const mic = { stop: vi.fn(async () => undefined), level: () => level };
      mics.push(mic);
      return mic;
    });
    render(<VoiceAsk portfolioId="laura" />);
    openVoice();
    await flush();
    act(() => FakeSocket.last?.receive({ type: "final", text: "¿Voy bien?" }));
    await flush();
    await waitFor(() => expect(screen.getByRole("status").textContent).toBe("Respondiendo en voz alta…"));
    await waitFor(() => expect(startMicrophone).toHaveBeenCalledTimes(2)); // el de vigilar el corte
    const before = new ArrayBuffer(8);
    sinks[1]?.(before); // lo que dice justo antes de detectarse su voz

    level = 0.6; // el usuario habla por encima
    await waitFor(() => expect(pause).toHaveBeenCalled());
    expect(screen.getByRole("status").textContent).toBe("Te escucho…");
    expect(screen.getByText("Has cortado la lectura. La respuesta queda aquí entera.")).toBeTruthy();
    expect(sentence("Segunda frase.")).toBeTruthy();
    // El mismo micrófono pasa a la transcripción (no se abre otro ni se cierra) con lo ya grabado.
    expect(startMicrophone).toHaveBeenCalledTimes(2);
    expect(mics[1]?.stop).not.toHaveBeenCalled();
    const ws = FakeSocket.last as FakeSocket;
    expect(JSON.parse(ws.sent[0] as string)).toMatchObject({ type: "start" });
    expect(ws.sent[1]).toBe(before);
    const after = new ArrayBuffer(4);
    sinks[1]?.(after);
    expect(ws.sent.at(-1)).toBe(after);
  });

  it("«Reiniciar el chat» borra la conversación", async () => {
    render(<VoiceAsk portfolioId="laura" />);
    const restart = screen.getByRole("button", { name: "Reiniciar el chat" });
    expect((restart as HTMLButtonElement).disabled).toBe(true);
    typeAndSend("¿Voy bien?");
    await flush();
    expect(sentence("Primera frase.")).toBeTruthy();
    fireEvent.click(restart);
    expect(sentences("Primera frase.")).toHaveLength(0);
    expect(screen.getByRole("heading", { name: "¿Qué quieres saber de tu cartera?" })).toBeTruthy();
  });

  it("la cruz y Escape cierran el asistente", () => {
    const onClose = vi.fn();
    render(<VoiceAsk portfolioId="laura" onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Cerrar el asistente" }));
    fireEvent.keyDown(screen.getByLabelText("Escribe tu pregunta"), { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it("sin micrófono ofrece el plan B", async () => {
    startMicrophone.mockRejectedValue(new MicrophoneDeniedError("denegado"));
    render(<VoiceAsk portfolioId="laura" />);
    openVoice();
    await flush();
    expect(screen.getByRole("alert").textContent).toMatch(/No puedo usar el micrófono/);
    expect(screen.getByLabelText("Escribe tu pregunta").closest("[inert]")).toBeNull();
    openVoice();
    await flush();
    expect(startMicrophone).toHaveBeenCalledTimes(2);

  });

  it("si la transcripción falla, dice que no ha entendido", async () => {
    startMicrophone.mockResolvedValue({ stop: vi.fn(async () => undefined) });
    render(<VoiceAsk portfolioId="laura" />);
    openVoice();
    await flush();
    act(() => FakeSocket.last?.receive({ type: "error", code: "UPSTREAM_UNAVAILABLE", message: "x" }));
    expect(screen.getByRole("alert").textContent).toMatch(/No te he entendido/);
    expect(askCalls).toHaveLength(0);
  });
});
