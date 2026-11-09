/**
 * El asistente: pregunta por voz (RF-14) o por texto (RF-15) sobre la cartera elegida, en
 * formato chat. Ocupa todo el alto de su contenedor (el panel lateral en escritorio, el modal en
 * móvil; ver `ChatDock`).
 *
 * - Cabecera con la marca del asistente, «Reiniciar el chat» y la cruz para cerrar (también Escape).
 * - La esfera (`VoiceStage`), siempre arriba: tocarla activa el modo conversación
 *   (`useConversation`), en el que se habla por turnos sin pulsar nada y se le puede cortar
 *   hablando. «Terminar la conversación» lo desactiva.
 * - La conversación, debajo, con scroll y barra propios: lo que se dicta aparece como burbuja del
 *   usuario y la respuesta se escribe palabra a palabra.
 * - La barra para escribir solo está fuera del modo conversación.
 */
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import "./chat.css";
import { Scrollbar } from "../components/Scrollbar";
import { ChatBackdrop } from "./ChatBackdrop";
import { ChatLogo } from "./ChatLogo";
import { ChatMessages } from "./ChatMessages";
import { Composer } from "./Composer";
import { CloseIcon, RestartIcon } from "./icons";
import { SpeakToggle } from "./SpeakToggle";
import { useConversation } from "./useConversation";
import { useSpeakPreference } from "./useSpeakPreference";
import { useVoiceAsk, type Phase } from "./useVoiceAsk";
import { VoiceStage } from "./VoiceStage";

const STATUS: Record<Phase, string> = {
  idle: "",
  listening: "Te escucho…",
  transcribing: "Transcribiendo…",
  thinking: "Pensando la respuesta…",
  speaking: "Respondiendo en voz alta…",
};

export const CHAT_TITLE_ID = "chat-title";

function prefersReducedMotion(): boolean {
  return typeof window.matchMedia === "function"
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : true;
}

function Welcome() {
  return (
    <section className="chat-fade my-auto flex flex-col items-center gap-3 px-2 py-6 text-center">
      <h3 className="m-0 text-xl font-semibold text-ink">¿Qué quieres saber de tu cartera?</h3>
      <p className="m-0 max-w-xs text-base text-ink-muted">
        Escribe tu pregunta o toca la esfera para hablar conmigo. Te respondo con las cifras de tu
        cartera.
      </p>
    </section>
  );
}

interface VoiceAskProps {
  portfolioId: string;
  /** Cierra el asistente (la cruz o Escape). Si no se pasa, no hay cruz. */
  onClose?: () => void;
}

export function VoiceAsk({ portfolioId, onClose }: VoiceAskProps) {
  const [speak, setSpeak] = useSpeakPreference();
  const [talking, setTalking] = useState(false);
  // En el modo conversación las respuestas siempre se leen en voz alta.
  const voice = useVoiceAsk(portfolioId, speak || talking);
  const { phase, partial, turns, problem, pressStart, pressEnd, giveUp, endVoice, ask, cancel, reset, getLevel } =
    voice;
  // Sin micrófono no hay conversación: se vuelve a la barra de texto.
  const conversation = talking && problem?.kind !== "mic";
  useConversation({
    active: conversation,
    phase,
    problem,
    listen: pressStart,
    playbackLevel: voice.playbackLevel,
  });

  const draft = conversation && (phase === "listening" || phase === "transcribing") ? partial : null;
  const scroller = useRef<HTMLDivElement>(null);
  const last = turns.at(-1);

  // Al llegar una pregunta, una frase o texto dictado, la conversación baja hasta lo último.
  useEffect(() => {
    const el = scroller.current;
    if ((!last && draft === null) || !el) return;
    el.scrollTo?.({ top: el.scrollHeight, behavior: prefersReducedMotion() ? "auto" : "smooth" });
  }, [last?.id, last?.sentences.length, last?.done, last, draft]);

  const askText = (question: string) => void ask(question, "text");
  const startConversation = () => {
    setTalking(true);
    pressStart();
  };
  const stopConversation = () => {
    endVoice();
    setTalking(false);
  };
  const restart = () => {
    reset();
    setTalking(false);
  };
  const close = () => {
    cancel();
    setTalking(false);
    onClose?.();
  };
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape" && onClose) {
      e.stopPropagation();
      close();
    }
  };

  return (
    <div onKeyDown={onKeyDown} className="relative isolate flex h-full min-h-0 flex-col">
      <ChatBackdrop />

      <header className="flex shrink-0 items-center gap-3 px-4 pb-1 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <ChatLogo className="size-10" />
        <div className="min-w-0 flex-1">
          <h2 id={CHAT_TITLE_ID} className="m-0 text-lg font-semibold leading-tight text-ink">
            Pregunta a Kairos
          </h2>
          <p className="m-0 text-sm leading-snug text-ink-muted">Asistente con IA · Por texto o por voz</p>
        </div>
        <button
          type="button"
          onClick={restart}
          disabled={turns.length === 0 && !conversation}
          aria-label="Reiniciar el chat"
          title="Reiniciar el chat"
          className="grid size-11 shrink-0 cursor-pointer place-items-center rounded-full text-ink-muted transition-[color,background-color,rotate] duration-300 hover:-rotate-90 hover:bg-surface-muted hover:text-ink disabled:cursor-default disabled:opacity-40 disabled:hover:rotate-0 disabled:hover:bg-transparent"
        >
          <RestartIcon className="size-5" />
        </button>
        {onClose && (
          <button
            type="button"
            onClick={close}
            aria-label="Cerrar el asistente"
            className="grid size-11 shrink-0 cursor-pointer place-items-center rounded-full text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink"
          >
            <CloseIcon className="size-5" />
          </button>
        )}
      </header>

      <VoiceStage
        active={conversation}
        phase={phase}
        problem={problem}
        getLevel={getLevel}
        onStart={startConversation}
        onStop={stopConversation}
        onFinish={() => void pressEnd()}
        onNothing={giveUp}
      />

      <div className="relative flex min-h-0 flex-1 flex-col">
        <div ref={scroller} className="kairos-scroll flex min-h-0 flex-1 flex-col overflow-y-auto px-4 pb-4 pt-3">
          {turns.length === 0 && draft === null ? (
            <Welcome />
          ) : (
            <ChatMessages turns={turns} phase={phase} onStop={cancel} draft={draft} />
          )}
        </div>
        <Scrollbar target={scroller} />
      </div>

      <div className="flex shrink-0 flex-col gap-2 px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2">
        {/* La barra de texto se recoge en el modo conversación (y vuelve al salir). */}
        <div
          inert={conversation}
          className={`grid transition-[grid-template-rows,opacity] duration-300 ease-out motion-reduce:transition-none ${
            conversation ? "grid-rows-[0fr] opacity-0" : "grid-rows-[1fr] opacity-100"
          }`}
        >
          <div className="flex min-h-0 flex-col gap-2 overflow-hidden p-0.5">
            {problem && !conversation && (
              <p role="alert" className="chat-fade m-0 rounded-control bg-warn-bg px-4 py-2.5 text-sm text-warn">
                {problem.message}
              </p>
            )}
            <Composer onAsk={askText} leading={<SpeakToggle on={speak} onChange={setSpeak} />} />
          </div>
        </div>
        <p className="m-0 text-center text-xs text-ink-muted">
          Respuestas generadas por IA. No es asesoramiento financiero.
        </p>
      </div>

      <p role="status" aria-live="polite" className="sr-only">
        {STATUS[phase]}
      </p>
    </div>
  );
}
