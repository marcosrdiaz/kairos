/**
 * Interruptor «Leer en voz alta»: si está activo, las respuestas también suenan. Es un
 * `role="switch"` con su nombre accesible; la preferencia la guarda `useSpeakPreference`.
 */
import { SpeakerIcon, SpeakerOffIcon } from "./icons";

interface SpeakToggleProps {
  on: boolean;
  onChange: (on: boolean) => void;
}

/**
 * Versión compacta para móvil, integrada en la barra de escritura: un botón redondo con el
 * altavoz (tachado si está apagado). Mismo `role="switch"` y nombre accesible.
 */
export function SpeakToggleCompact({ on, onChange }: SpeakToggleProps) {
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

export function SpeakToggle({ on, onChange }: SpeakToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label="Leer las respuestas en voz alta"
      onClick={() => onChange(!on)}
      className={`inline-flex min-h-touch shrink-0 cursor-pointer items-center gap-2.5 rounded-full border px-3 text-sm font-semibold transition-colors ${
        on
          ? "border-accent bg-accent-tint text-ink"
          : "border-line-strong bg-surface text-ink-muted hover:text-ink"
      }`}
    >
      {on ? <SpeakerIcon className="size-5" /> : <SpeakerOffIcon className="size-5" />}
      <span aria-hidden="true" className="hidden sm:inline">
        Leer en voz alta
      </span>
      <span
        aria-hidden="true"
        className={`relative block h-5 w-9 shrink-0 rounded-full transition-colors ${on ? "bg-accent" : "bg-line-strong"}`}
      >
        <span
          className={`absolute left-0.5 top-0.5 block size-4 rounded-full shadow transition-transform motion-reduce:transition-none ${
            on ? "translate-x-4 bg-on-accent" : "translate-x-0 bg-surface"
          }`}
        />
      </span>
    </button>
  );
}
