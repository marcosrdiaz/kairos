/**
 * Pregunta por voz (RF-14) o por texto (RF-15) sobre la cartera elegida.
 *
 * - Mantener pulsado el micrófono (ratón, dedo, o Espacio/Intro con el teclado) para hablar.
 * - Las frases llegan ya aprobadas por el guardián; se muestran según llegan y suenan en orden.
 * - Plan B siempre a mano: preguntas sugeridas y campo de texto.
 */
import { useId, useState, type FormEvent, type KeyboardEvent, type PointerEvent } from "react";
import { buttonPrimary, buttonSecondary } from "../components/button";
import { AI_DISCLAIMER, SUGGESTED_QUESTIONS } from "./texts";
import { useVoiceAsk, type Phase } from "./useVoiceAsk";

const STATUS: Record<Phase, string> = {
  idle: "",
  listening: "Te escucho…",
  transcribing: "Transcribiendo…",
  thinking: "Pensando la respuesta…",
  speaking: "Respondiendo…",
};

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="size-9" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
    </svg>
  ); // prettier-ignore
}

export function VoiceAsk({ portfolioId }: { portfolioId: string }) {
  const [speakText, setSpeakText] = useState(true);
  const [draft, setDraft] = useState("");
  const { phase, partial, turn, problem, pressStart, pressEnd, ask, cancel } = useVoiceAsk(
    portfolioId,
    speakText,
  );
  const hintId = useId();
  const listening = phase === "listening";
  const busy = phase === "thinking" || phase === "speaking";

  const onPointerDown = (e: PointerEvent<HTMLButtonElement>) => {
    if (e.button !== 0) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    pressStart();
  };
  const onKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    if ((e.key === " " || e.key === "Enter") && !e.repeat) {
      e.preventDefault();
      pressStart();
    }
  };
  const onKeyUp = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      void pressEnd();
    }
  };
  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const question = draft.trim();
    if (!question) return;
    setDraft("");
    void ask(question, "text");
  };

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col items-center gap-4 rounded-card border border-line bg-surface p-6 text-center">
        <button
          type="button"
          aria-pressed={listening}
          aria-describedby={hintId}
          onPointerDown={onPointerDown}
          onPointerUp={() => void pressEnd()}
          onPointerCancel={() => void pressEnd()}
          onKeyDown={onKeyDown}
          onKeyUp={onKeyUp}
          onContextMenu={(e) => e.preventDefault()}
          className={`relative grid size-24 touch-none select-none place-items-center rounded-full transition-transform ${
            listening
              ? "scale-105 bg-accent-hover text-on-accent"
              : "bg-accent text-on-accent hover:bg-accent-hover"
          }`}
        >
          {listening && (
            <span
              aria-hidden="true"
              className="absolute inset-0 rounded-full border-4 border-gold motion-safe:animate-ping"
            />
          )}
          <MicIcon />
          <span className="sr-only">Hablar</span>
        </button>
        <p id={hintId} className="m-0 text-ink-muted">
          {listening ? "Suelta para preguntar" : "Mantén pulsado y pregunta"}
        </p>
        <p role="status" aria-live="polite" className="m-0 min-h-[1.5em] font-medium text-ink">
          {STATUS[phase]}
        </p>
        {partial && <p className="m-0 text-lg italic text-ink-muted">«{partial}»</p>}
      </section>

      {problem && (
        <p role="alert" className="m-0 rounded-card bg-warn-bg p-4 text-warn">
          {problem.message}
        </p>
      )}

      {turn && (
        <section aria-label="Respuesta" className="flex flex-col gap-3 rounded-card border border-line bg-surface p-5">
          <p className="m-0 self-end rounded-card bg-accent-tint px-4 py-2 text-ink">{turn.question}</p>
          {turn.showDisclaimer && <p className="m-0 text-sm text-ink-muted">{AI_DISCLAIMER}</p>}
          <div aria-live="polite" className="flex flex-col gap-2 text-lg text-ink">
            {turn.sentences.map((s) => (
              <p key={s.index} className="m-0" data-calc-ids={s.calcIds.join(" ") || undefined}>
                {s.text}
              </p>
            ))}
          </div>
          {!turn.done && turn.sentences.length === 0 && (
            <p className="m-0 text-ink-muted">Preparando la respuesta…</p>
          )}
          {turn.error && <p role="alert" className="m-0 text-error">{turn.error}</p>}
          {turn.ttsFailed && (
            <p className="m-0 text-sm text-ink-muted">
              No he podido leer la respuesta en voz alta; aquí la tienes en texto.
            </p>
          )}
          {busy && (
            <button type="button" onClick={cancel} className={`${buttonSecondary} self-start`}>
              Parar
            </button>
          )}
        </section>
      )}

      <section aria-labelledby="suggested-title" className="flex flex-col gap-3">
        <h2 id="suggested-title" className="m-0 text-lg font-semibold text-ink">
          O elige una pregunta
        </h2>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button key={q} type="button" className={buttonSecondary} onClick={() => void ask(q, "text")}>
              {q}
            </button>
          ))}
        </div>
        <form onSubmit={onSubmit} className="flex flex-wrap gap-2">
          <label htmlFor="ask-text" className="sr-only">
            Escribe tu pregunta
          </label>
          <input
            id="ask-text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Escribe tu pregunta"
            maxLength={300}
            className="min-h-touch min-w-0 flex-1 rounded-control border border-line-strong bg-surface px-4 text-base text-ink"
          />
          <button type="submit" className={buttonPrimary}>
            Preguntar
          </button>
        </form>
        <label className="flex min-h-touch items-center gap-2 text-ink">
          <input type="checkbox" checked={speakText} onChange={(e) => setSpeakText(e.target.checked)} className="size-5" />
          Leer también en voz alta las respuestas escritas
        </label>
      </section>

      <p className="m-0 text-sm text-ink-muted">
        Respuestas generadas por IA a partir de los datos de tu cartera. No es asesoramiento financiero.
      </p>
    </div>
  );
}
