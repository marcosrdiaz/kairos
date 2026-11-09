/**
 * Barra para preguntar por escrito, al pie del asistente (se oculta en el modo conversación).
 * A la izquierda, el control `leading` (el interruptor «Leer en voz alta»); a la derecha,
 * «Enviar», desactivado mientras el campo está vacío. Intro también envía; Mayús+Intro, salto
 * de línea. Para hablar se usa la esfera de arriba.
 */
import { useRef, useState, type FormEvent, type KeyboardEvent, type ReactNode } from "react";
import { SendIcon } from "./icons";

const MAX_TEXTAREA_PX = 160;

interface ComposerProps {
  onAsk: (question: string) => void;
  leading?: ReactNode;
}

export function Composer({ onAsk, leading }: ComposerProps) {
  const [draft, setDraft] = useState("");
  const textarea = useRef<HTMLTextAreaElement>(null);
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

  return (
    <form
      onSubmit={submit}
      className={`flex items-end gap-1.5 rounded-[1.75rem] border border-line-strong bg-surface p-1.5 ${leading ? "" : "pl-4"} shadow-[0_6px_24px_-12px_rgb(0_0_0/0.35)] transition-colors focus-within:border-accent`}
    >
      {leading && <div className="flex shrink-0">{leading}</div>}
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
        className="kairos-scroll min-h-11 min-w-0 flex-1 resize-none border-0 bg-transparent py-2.5 text-base leading-6 text-ink placeholder:text-ink-muted focus:outline-none"
      />
      <button
        type="submit"
        aria-label="Enviar pregunta"
        disabled={!hasText}
        className="grid size-11 shrink-0 cursor-pointer place-items-center rounded-full bg-accent text-on-accent transition-[background-color,opacity,scale] duration-200 hover:bg-accent-hover active:scale-95 disabled:cursor-not-allowed disabled:bg-line-strong disabled:opacity-50 disabled:active:scale-100"
      >
        <SendIcon className="size-5" />
      </button>
    </form>
  );
}
