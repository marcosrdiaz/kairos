/**
 * La esfera del asistente, siempre arriba de la conversación (la franja no tapa los mensajes ni
 * al revés). Es también el botón del modo conversación:
 *
 * - Fuera del modo conversación: tocarla lo activa y empieza a escuchar (con efecto al pasar el
 *   ratón). También si la conversación está en pausa por un problema.
 * - En el modo conversación se mueve con la voz del usuario al escuchar y con la de la respuesta
 *   al leerla. Mientras responde, tocarla corta la respuesta y vuelve a escuchar (además de
 *   cortarla hablando). Aparece «Terminar la conversación» para salir.
 * - Al escuchar: tras hablar, una pausa de `SILENCE_MS` (2 s) termina la pregunta; si no se oye
 *   nada en `NO_SPEECH_MS`, se deja de escuchar sin transcribir; tope de `MAX_RECORDING_MS`.
 */
import { useEffect, useRef } from "react";
import { StopIcon } from "./icons";
import { MAX_RECORDING_MS, type Phase, type Problem } from "./useVoiceAsk";
import { VoiceDial } from "./VoiceDial";

/** Pausa tras la voz que da la pregunta por terminada. */
export const SILENCE_MS = 2000;
/** Si en este tiempo no se oye nada, se deja de escuchar. */
export const NO_SPEECH_MS = 8000;
/** Volumen (0-1, `getLevel`) a partir del cual se considera que hay voz. */
export const SPEECH_LEVEL = 0.12;
const CHECK_EVERY_MS = 100;

interface WatchProps {
  getLevel: () => number;
  /** Se habló y llegó la pausa (o el tope): hay que transcribir. */
  onDone: () => void;
  /** No se oyó nada. */
  onNothing: () => void;
}

/**
 * Vigila el volumen mientras se escucha y avisa una sola vez. Se monta al empezar a escuchar,
 * así que cada escucha parte de cero. No pinta nada.
 */
function ListeningWatch({ getLevel, onDone, onNothing }: WatchProps) {
  const handlers = useRef({ onDone, onNothing });
  useEffect(() => {
    handlers.current = { onDone, onNothing };
  });
  useEffect(() => {
    const startedAt = Date.now();
    let lastVoiceAt: number | null = null;
    const timer = window.setInterval(() => {
      const now = Date.now();
      if (getLevel() >= SPEECH_LEVEL) lastVoiceAt = now;
      if (lastVoiceAt === null && now - startedAt >= NO_SPEECH_MS) {
        window.clearInterval(timer);
        handlers.current.onNothing();
      } else if (
        (lastVoiceAt !== null && now - lastVoiceAt >= SILENCE_MS) ||
        now - startedAt >= MAX_RECORDING_MS
      ) {
        window.clearInterval(timer);
        handlers.current.onDone();
      }
    }, CHECK_EVERY_MS);
    return () => window.clearInterval(timer);
  }, [getLevel]);
  return null;
}

const STATUS: Record<Phase, string> = {
  idle: "En conversación",
  listening: "Te escucho… Haz una pausa al acabar",
  transcribing: "Transcribiendo…",
  thinking: "Pensando… Habla o toca la esfera para cortar",
  speaking: "Respondiendo · Habla o toca la esfera para cortar",
};

interface VoiceStageProps {
  /** Modo conversación activo. */
  active: boolean;
  phase: Phase;
  problem: Problem | null;
  getLevel: () => number;
  onStart: () => void;
  onStop: () => void;
  onFinish: () => void;
  onNothing: () => void;
}

export function VoiceStage(props: VoiceStageProps) {
  const { active, phase, problem, getLevel, onStart, onStop, onFinish, onNothing } = props;
  const paused = active && problem !== null && phase === "idle";
  const answering = active && (phase === "thinking" || phase === "speaking");
  const clickable = !active || paused || answering;
  const label = answering ? "Interrumpir la respuesta y hablar" : paused ? "Volver a escuchar" : "Empezar a hablar con Kairos";
  const dial = <VoiceDial mode={active ? phase : "idle"} getLevel={getLevel} className="size-32 sm:size-36" />;
  const status = !active ? "Toca la esfera para hablar conmigo" : paused ? "Conversación en pausa" : STATUS[phase];

  return (
    <section aria-label="Conversación por voz" className="flex shrink-0 flex-col items-center gap-1.5 border-b border-line/70 px-4 pb-3">
      {clickable ? (
        <button
          type="button"
          onClick={onStart}
          aria-label={label}
          className="voice-dial-button group cursor-pointer rounded-full transition-transform duration-300 ease-out hover:scale-[1.04] active:scale-95"
        >
          {dial}
        </button>
      ) : (
        <div>{dial}</div>
      )}

      <p className="m-0 text-center text-sm font-medium text-ink-muted" aria-hidden={!active}>
        {status}
      </p>
      {problem && active && (
        <p role="alert" className="chat-fade m-0 rounded-control bg-warn-bg px-3 py-1.5 text-center text-sm text-warn">
          {problem.message}
        </p>
      )}
      {active && (
        <button
          type="button"
          onClick={onStop}
          className="chat-fade mt-1 inline-flex min-h-touch cursor-pointer items-center gap-2 rounded-full border border-line-strong bg-surface px-4 text-sm font-semibold text-ink shadow-sm transition-colors hover:border-accent hover:bg-accent-tint"
        >
          <StopIcon className="size-4" />
          Terminar la conversación
        </button>
      )}
      {active && phase === "listening" && <ListeningWatch getLevel={getLevel} onDone={onFinish} onNothing={onNothing} />}
    </section>
  );
}
