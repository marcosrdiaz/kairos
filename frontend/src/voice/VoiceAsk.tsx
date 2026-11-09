/**
 * Pregunta por voz (RF-14) o por texto (RF-15) sobre la cartera elegida, en formato chat.
 *
 * - Título solo para lectores de pantalla. Interruptor «Leer en voz alta»: arriba a la derecha en
 *   escritorio y dentro de la barra en móvil (versión compacta; la oculta no llega al lector).
 * - Conversación con historial (o la bienvenida con las preguntas sugeridas).
 * - Barra fija abajo: en móvil, encima de las pestañas; en escritorio, al pie de la pantalla.
 *   Ocupa todo el ancho, como Inicio. En móvil, la bienvenida cabe sin scroll (también en 375×667).
 *   Las sugerencias quedan siempre a mano encima de la barra (plan B de la voz).
 */
import { useEffect, useRef } from "react";
import "./chat.css";
import { ChatMessages } from "./ChatMessages";
import { Composer } from "./Composer";
import { SpeakToggle, SpeakToggleCompact } from "./SpeakToggle";
import { useSpeakPreference } from "./useSpeakPreference";
import { EmptyChat, SuggestionChips } from "./Suggestions";
import { useVoiceAsk, type Phase } from "./useVoiceAsk";

const STATUS: Record<Phase, string> = {
  idle: "",
  listening: "Te escucho…",
  transcribing: "Transcribiendo…",
  thinking: "Pensando la respuesta…",
  speaking: "Respondiendo en voz alta…",
};

function prefersReducedMotion(): boolean {
  return typeof window.matchMedia === "function"
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : true;
}

export function VoiceAsk({ portfolioId }: { portfolioId: string }) {
  const [speak, setSpeak] = useSpeakPreference();
  const { phase, partial, turns, problem, pressStart, pressEnd, ask, cancel } = useVoiceAsk(
    portfolioId,
    speak,
  );
  const end = useRef<HTMLDivElement>(null);
  const last = turns.at(-1);

  // Al llegar una pregunta o una frase nueva, la conversación baja hasta lo último.
  useEffect(() => {
    if (!last) return;
    end.current?.scrollIntoView?.({
      block: "end",
      behavior: prefersReducedMotion() ? "auto" : "smooth",
    });
  }, [last?.id, last?.sentences.length, last?.done, last]);

  const askText = (question: string) => void ask(question, "text");

  return (
    // El <main> de AppShell deja un relleno inferior (móvil: pestañas + 1,5rem; escritorio: 3rem).
    // Se compensa con margen negativo para que la barra quede pegada abajo con su propio margen,
    // y la altura mínima llena la pantalla aunque haya pocos mensajes.
    <div className="-mb-6 flex min-h-[calc(100dvh-var(--kairos-header-height)-var(--kairos-bottom-nav-height)-1.5rem)] w-full flex-col lg:-mb-12 lg:min-h-[calc(100dvh-2.5rem)]">
      <h1 className="sr-only">Pregunta</h1>
      {/* Escritorio: interruptor arriba a la derecha. En móvil va dentro de la barra (no resta alto). */}
      <div className="hidden justify-end pb-4 lg:flex">
        <SpeakToggle on={speak} onChange={setSpeak} />
      </div>

      <div className="flex flex-1 flex-col pb-4">
        {turns.length === 0 ? (
          <div className="my-auto">
            <EmptyChat onPick={askText} />
          </div>
        ) : (
          <ChatMessages turns={turns} phase={phase} onStop={cancel} />
        )}
        <div ref={end} className="scroll-mb-56" />
      </div>

      <div className="sticky bottom-(--kairos-bottom-nav-height) z-10 -mx-4 flex flex-col gap-2 bg-linear-to-t from-paper from-80% to-transparent px-4 pb-3 pt-3 sm:pt-6 lg:bottom-0 lg:pb-4">
        {problem && (
          <p role="alert" className="chat-fade m-0 rounded-control bg-warn-bg px-4 py-2.5 text-sm text-warn">
            {problem.message}
          </p>
        )}
        {turns.length > 0 && <SuggestionChips onPick={askText} />}
        <Composer
          phase={phase}
          partial={partial}
          onAsk={askText}
          onPressStart={pressStart}
          onPressEnd={() => void pressEnd()}
          leading={<SpeakToggleCompact on={speak} onChange={setSpeak} />}
        />
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
