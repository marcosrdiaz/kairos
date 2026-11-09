/**
 * Interruptor «Leer en voz alta», integrado en la barra de escritura (escritorio y móvil): un
 * botón redondo con el altavoz (tachado si está apagado). Es un `role="switch"` con su nombre
 * accesible; la preferencia la guarda `useSpeakPreference`.
 */
import { SpeakerIcon, SpeakerOffIcon } from "./icons";

interface SpeakToggleProps {
  on: boolean;
  onChange: (on: boolean) => void;
}

export function SpeakToggle({ on, onChange }: SpeakToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label="Leer las respuestas en voz alta"
      onClick={() => onChange(!on)}
      className={`grid size-11 shrink-0 cursor-pointer place-items-center rounded-full transition-colors ${
        on ? "bg-accent-tint text-accent" : "text-ink-muted hover:bg-surface-muted hover:text-ink"
      }`}
    >
      {on ? <SpeakerIcon className="size-5" /> : <SpeakerOffIcon className="size-5" />}
    </button>
  );
}
