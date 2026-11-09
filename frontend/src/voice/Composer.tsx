/**
 * Barra para preguntar, fija abajo. Un solo botón a la derecha:
 * - sin texto: micrófono, que se mantiene pulsado (ratón, dedo, o Espacio/Intro) para hablar;
 * - con texto: enviar (Intro también envía; Mayús+Intro, salto de línea).
 * Mientras se habla, la barra muestra «Te escucho…» y lo que se va transcribiendo.
 */
import {
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type PointerEvent,
  type ReactNode,
} from "react";
import { MicIcon, SendIcon } from "./icons";
import type { Phase } from "./useVoiceAsk";

const MAX_TEXTAREA_PX = 160;

interface ComposerProps {
  phase: Phase;
  partial: string;
  onAsk: (question: string) => void;
  onPressStart: () => void;
  onPressEnd: () => void;
  /** Control a la izquierda, solo en móvil (el interruptor de voz compacto). */
  leading?: ReactNode;
}

export function Composer({ phase, partial, onAsk, onPressStart, onPressEnd, leading }: ComposerProps) {
  const [draft, setDraft] = useState("");
  const textarea = useRef<HTMLTextAreaElement>(null);
  const listening = phase === "listening";
  const capturing = listening || phase === "transcribing";
  const hasText = draft.trim().length > 0;

  const resize = () => {
    const el = textarea.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_TEXTAREA_PX)}px`;
  };

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const question = draft.trim();
    if (!question) return;
    setDraft("");
    requestAnimationFrame(resize);
    onAsk(question);
  };

  const onTextKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) submit(e);
  };

  const onMicPointerDown = (e: PointerEvent<HTMLButtonElement>) => {
    if (e.button !== 0) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    onPressStart();
  };
  const onMicKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    if ((e.key === " " || e.key === "Enter") && !e.repeat) {
      e.preventDefault();
      onPressStart();
    }
  };
  const onMicKeyUp = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      onPressEnd();
    }
  };

  return (
    <form
      onSubmit={submit}
      className={`flex items-end gap-2 rounded-[1.75rem] border bg-surface p-1.5 ${leading ? "pl-1.5 lg:pl-4" : "pl-4"} shadow-[0_6px_24px_-12px_rgb(0_0_0/0.35)] transition-colors ${
        capturing ? "border-accent" : "border-line-strong focus-within:border-accent"
      }`}
    >
      {leading && <div className="flex shrink-0 lg:hidden">{leading}</div>}
      {capturing ? (
        <div className="chat-fade flex min-h-11 min-w-0 flex-1 items-center gap-2.5 py-2" aria-hidden="true">
          <span className="relative flex size-3 shrink-0">
            <span className="absolute inset-0 rounded-full bg-accent opacity-60 motion-safe:animate-ping" />
            <span className="relative size-3 rounded-full bg-accent" />
          </span>
          <span className="min-w-0 truncate text-base text-ink">
            {partial ? `«${partial}»` : listening ? "Te escucho…" : "Transcribiendo…"}
          </span>
        </div>
      ) : (
        <>
          <label htmlFor="ask-text" className="sr-only">
            Escribe tu pregunta
          </label>
          <textarea
            id="ask-text"
            ref={textarea}
            rows={1}
            value={draft}
            maxLength={300}
            placeholder="Pregunta sobre tu cartera…"
            onChange={(e) => {
              setDraft(e.target.value);
              resize();
            }}
            onKeyDown={onTextKeyDown}
            className="min-h-11 min-w-0 flex-1 resize-none border-0 bg-transparent py-2.5 text-base leading-6 text-ink placeholder:text-ink-muted focus:outline-none"
          />
        </>
      )}

      {hasText && !capturing ? (
        <button
          type="submit"
          aria-label="Enviar pregunta"
          className="grid size-11 shrink-0 cursor-pointer place-items-center rounded-full bg-accent text-on-accent hover:bg-accent-hover"
        >
          <SendIcon className="size-5" />
        </button>
      ) : (
        <button
          type="button"
          aria-label="Mantén pulsado para hablar"
          aria-pressed={listening}
          onPointerDown={onMicPointerDown}
          onPointerUp={onPressEnd}
          onPointerCancel={onPressEnd}
          onKeyDown={onMicKeyDown}
          onKeyUp={onMicKeyUp}
          onContextMenu={(e) => e.preventDefault()}
          className={`relative grid size-11 shrink-0 cursor-pointer touch-none select-none place-items-center rounded-full transition-transform ${
            listening
              ? "scale-110 bg-accent-hover text-on-accent"
              : "bg-accent text-on-accent hover:bg-accent-hover"
          }`}
        >
          {listening && (
            <span
              aria-hidden="true"
              className="absolute -inset-1.5 rounded-full border-2 border-accent motion-safe:animate-ping"
            />
          )}
          <MicIcon className="size-5" />
        </button>
      )}
    </form>
  );
}
