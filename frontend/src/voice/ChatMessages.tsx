/**
 * La conversación: la pregunta a la derecha y la respuesta de KAIROS a la izquierda.
 * Las frases entran línea a línea. Mientras se prepara la respuesta, puntos de "escribiendo";
 * mientras se lee en voz alta, un
 * indicador con «Parar». Todo el movimiento solo con `motion-safe`.
 */
import { useState, type CSSProperties } from "react";
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

/** Separación mínima entre la entrada de una línea y la siguiente. */
const LINE_STAGGER_MS = 450;

/**
 * Reparte el retardo de entrada de las líneas de un turno para que aparezcan una detrás de otra,
 * aunque el servidor mande varias frases a la vez. Si una frase llega más tarde que su hueco,
 * entra en cuanto llega (sin retardo acumulado).
 */
class LineScheduler {
  private nextAt = 0;
  delay(): number {
    const now = performance.now();
    const delay = Math.max(0, this.nextAt - now);
    this.nextAt = now + delay + LINE_STAGGER_MS;
    return Math.round(delay);
  }
}

/**
 * Una frase de la respuesta = una línea que "se va generando" (`chat.css`, `.chat-line`). El
 * retardo se fija al montarse, así que las líneas ya mostradas no se repiten al llegar otras.
 */
function GeneratedLine({ text, calcIds, scheduler }: { text: string; calcIds: string[]; scheduler: LineScheduler }) {
  const [delay] = useState(() => scheduler.delay());
  return (
    <p
      className="chat-line m-0"
      style={{ "--d": `${delay}ms` } as CSSProperties}
      data-calc-ids={calcIds.join(" ") || undefined}
    >
      {text}
    </p>
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
      <p className="chat-in-user m-0 max-w-[85%] self-end rounded-2xl rounded-br-md bg-accent px-4 py-2.5 text-base text-on-accent">
        <span className="sr-only">Tú: </span>
        {turn.question}
      </p>

      <div className="chat-in-bot flex max-w-full items-start gap-2.5 sm:max-w-[90%]">
        <LogoTile className="mt-0.5 size-9" />
        <div className="flex min-w-0 flex-1 flex-col gap-2 rounded-2xl rounded-tl-md border border-line bg-surface px-4 py-3">
          <span className="sr-only">KAIROS: </span>
          {turn.showDisclaimer && (
            <p className="m-0 flex items-start gap-1.5 text-sm text-ink-muted">
              <InfoIcon className="mt-0.5 size-4 shrink-0" />
              {AI_DISCLAIMER}
            </p>
          )}
          {waiting && <TypingDots />}
          {turn.sentences.length > 0 && (
            <div className="flex flex-col gap-2 text-lg leading-relaxed text-ink">
              {turn.sentences.map((s) => (
                <GeneratedLine key={s.index} text={s.text} calcIds={s.calcIds} scheduler={scheduler} />
              ))}
            </div>
          )}
          {turn.error && (
            <p role="alert" className="chat-fade m-0 text-base text-error">
              {turn.error}
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
}

export function ChatMessages({ turns, phase, onStop }: ChatMessagesProps) {
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
    </ol>
  );
}
