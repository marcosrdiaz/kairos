/**
 * La conversación: la pregunta a la derecha y la respuesta de KAIROS a la izquierda.
 * La respuesta se escribe palabra a palabra, con todas las frases seguidas en un párrafo.
 * Mientras se prepara, puntos de "escribiendo"; mientras se lee en voz alta, un indicador con
 * «Parar». En el modo voz, lo que se va transcribiendo aparece como una burbuja del usuario
 * (`draft`). El movimiento, solo sin `prefers-reduced-motion` (`chat.css`).
 */
import { Fragment, useState, type CSSProperties } from "react";
import { LogoTile } from "../components/icons";
import { InfoIcon, StopIcon } from "./icons";
import { AI_DISCLAIMER } from "./texts";
import type { Phase, Turn } from "./useVoiceAsk";

function TypingDots() {
  return (
    <span className="flex items-center gap-1.5 py-2.5" aria-hidden="true">
      {[0, 160, 320].map((delay) => (
        <span
          key={delay}
          className="chat-dot size-2 rounded-full bg-ink-muted"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  );
}

/** Ritmo de escritura: cada palabra entra este tiempo después de la anterior. */
const WORD_MS = 45;

/**
 * Reparte el retardo de entrada de las frases de un turno para que se escriban una detrás de
 * otra, aunque el servidor mande varias a la vez. Si una frase llega cuando la anterior ya está
 * escrita, empieza en cuanto llega (sin retardo acumulado).
 */
class LineScheduler {
  private nextAt = 0;
  delay(durationMs: number): number {
    const now = performance.now();
    const delay = Math.max(0, this.nextAt - now);
    this.nextAt = now + delay + durationMs;
    return Math.round(delay);
  }
}

/**
 * Una frase de la respuesta, escrita palabra a palabra (`chat.css`, `.chat-word`) a
 * continuación de la anterior. Los retardos se fijan al montarse, así que lo ya escrito no se
 * repite al llegar otras frases.
 */
function GeneratedLine({ text, calcIds, scheduler }: { text: string; calcIds: string[]; scheduler: LineScheduler }) {
  const words = text.split(/\s+/).filter(Boolean);
  const [delay] = useState(() => scheduler.delay(words.length * WORD_MS));
  return (
    <span className="chat-line" data-calc-ids={calcIds.join(" ") || undefined}>
      {words.map((word, i) => (
        <Fragment key={i}>
          {i > 0 && " "}
          <span className="chat-word" style={{ "--d": `${delay + i * WORD_MS}ms` } as CSSProperties}>
            {word}
          </span>
        </Fragment>
      ))}
    </span>
  );
}

/** Lo que el usuario va diciendo, en su burbuja, con un cursor que parpadea. */
function DraftBubble({ text }: { text: string }) {
  return (
    <li className="flex flex-col">
      <p className="chat-in-user chat-bubble-user m-0 mr-1.5 max-w-[85%] self-end rounded-[1.25rem] rounded-br-none bg-accent px-4 py-2.5 text-base text-on-accent">
        <span className="sr-only">Tú, dictando: </span>
        {text ? <span>{text}</span> : <span className="opacity-75">Te escucho</span>}
        <span
          aria-hidden="true"
          className="chat-caret ml-0.5 inline-block h-[1.1em] w-0.5 translate-y-0.5 rounded-full bg-on-accent"
        />
      </p>
    </li>
  );
}

function SpeakingBars() {
  return (
    <span className="flex h-4 items-end gap-0.5" aria-hidden="true">
      {[0, 200, 400].map((delay) => (
        <span
          key={delay}
          className="h-full w-1 origin-bottom rounded-full bg-accent motion-safe:animate-pulse"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  );
}

interface TurnProps {
  turn: Turn;
  /** Fase del turno en curso, o `null` si este turno ya terminó. */
  activePhase: Phase | null;
  onStop: () => void;
}

function ChatTurn({ turn, activePhase, onStop }: TurnProps) {
  const thinking = activePhase === "thinking";
  const speaking = activePhase === "speaking";
  const waiting = turn.sentences.length === 0 && !turn.done && !turn.error;
  const [scheduler] = useState(() => new LineScheduler());
  return (
    <li className="flex flex-col gap-3">
      <p className="chat-in-user chat-bubble-user m-0 mr-1.5 max-w-[85%] self-end rounded-[1.25rem] rounded-br-none bg-accent px-4 py-2.5 text-base text-on-accent">
        <span className="sr-only">Tú: </span>
        {turn.question}
      </p>

      <div className="chat-in-bot flex max-w-full items-start gap-2.5 sm:max-w-[90%]">
        <LogoTile className="size-8" />
        <div className="chat-bubble-bot ml-1.5 flex min-w-0 flex-1 flex-col gap-2 rounded-[1.25rem] rounded-tl-none bg-surface px-4 py-3 shadow-[0_2px_10px_-4px_rgb(0_0_0/0.18)]">
          <span className="sr-only">KAIROS: </span>
          {turn.showDisclaimer && (
            <p className="m-0 flex items-start gap-1.5 text-sm text-ink-muted">
              <InfoIcon className="mt-0.5 size-4 shrink-0" />
              {AI_DISCLAIMER}
            </p>
          )}
          {waiting && <TypingDots />}
          {turn.sentences.length > 0 && (
            <p className="m-0 text-base leading-relaxed text-ink">
              {turn.sentences.map((s, i) => (
                <Fragment key={s.index}>
                  {i > 0 && " "}
                  <GeneratedLine text={s.text} calcIds={s.calcIds} scheduler={scheduler} />
                </Fragment>
              ))}
            </p>
          )}
          {turn.error && (
            <p role="alert" className="chat-fade m-0 text-base text-error">
              {turn.error}
            </p>
          )}
          {turn.interrupted && (
            <p className="chat-fade m-0 flex items-center gap-1.5 text-sm font-medium text-ink-muted">
              <StopIcon className="size-4 shrink-0" />
              Has cortado la lectura. La respuesta queda aquí entera.
            </p>
          )}
          {turn.ttsFailed && (
            <p className="chat-fade m-0 text-sm text-ink-muted">
              No he podido leer esta respuesta en voz alta; aquí la tienes en texto.
            </p>
          )}
          {(thinking || speaking) && (
            <div className="chat-fade mt-1 flex items-center justify-between gap-3 border-t border-line pt-2">
              <span className="flex items-center gap-2 text-sm text-ink-muted">
                {speaking ? <SpeakingBars /> : null}
                {speaking ? "Leyendo en voz alta" : "Preparando la respuesta…"}
              </span>
              <button
                type="button"
                onClick={onStop}
                className="inline-flex min-h-touch cursor-pointer items-center gap-1.5 rounded-full px-3 text-sm font-semibold text-ink hover:bg-surface-muted"
              >
                <StopIcon className="size-4" />
                Parar
              </button>
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

interface ChatMessagesProps {
  turns: Turn[];
  phase: Phase;
  onStop: () => void;
  /** Transcripción en curso del modo voz ("" si aún no hay texto); `null` si no se dicta. */
  draft?: string | null;
}

export function ChatMessages({ turns, phase, onStop, draft = null }: ChatMessagesProps) {
  const busy = phase === "thinking" || phase === "speaking";
  return (
    <ol aria-label="Conversación" aria-live="polite" className="m-0 flex list-none flex-col gap-6 p-0">
      {turns.map((turn, i) => (
        <ChatTurn
          key={turn.id}
          turn={turn}
          activePhase={busy && i === turns.length - 1 ? phase : null}
          onStop={onStop}
        />
      ))}
      {draft !== null && <DraftBubble text={draft} />}
    </ol>
  );
}
