/**
 * Preguntas sugeridas (plan B de la voz y atajo para empezar).
 * - `EmptyChat`: bienvenida con las sugerencias en tarjetas, antes de la primera pregunta.
 * - `SuggestionChips`: fila compacta encima de la barra cuando ya hay conversación (en móvil se
 *   desplaza en horizontal).
 */
import { LogoTile } from "../components/icons";
import { SUGGESTED_QUESTIONS } from "./texts";

interface SuggestionProps {
  onPick: (question: string) => void;
  disabled?: boolean;
}

export function EmptyChat({ onPick, disabled = false }: SuggestionProps) {
  return (
    <section
      aria-labelledby="chat-empty-title"
      className="flex flex-col items-center gap-4 py-2 text-center sm:gap-6 sm:py-12"
    >
      <LogoTile className="size-10 sm:size-14" />
      <div className="flex flex-col gap-1.5 sm:gap-2">
        <h2 id="chat-empty-title" className="m-0 text-lg font-semibold text-ink sm:text-2xl">
          ¿Qué quieres saber de tu cartera?
        </h2>
        <p className="m-0 max-w-md text-sm text-ink-muted sm:text-base [@media(max-height:700px)]:hidden">
          Pregunta por escrito o mantén pulsado el micrófono. Te respondo con las cifras de tu
          cartera.
        </p>
      </div>
      <ul className="m-0 grid w-full list-none gap-2 p-0 sm:grid-cols-3 sm:gap-3">
        {SUGGESTED_QUESTIONS.map((q) => (
          <li key={q} className="flex">
            <button
              type="button"
              disabled={disabled}
              onClick={() => onPick(q)}
              className="flex min-h-touch flex-1 cursor-pointer items-center justify-center rounded-card border border-line bg-surface px-4 py-2 text-base sm:py-3 font-semibold text-ink transition-colors hover:border-accent hover:bg-accent-tint disabled:cursor-not-allowed disabled:opacity-60"
            >
              {q}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function SuggestionChips({ onPick, disabled = false }: SuggestionProps) {
  return (
    <ul
      aria-label="Preguntas sugeridas"
      className="m-0 flex list-none gap-2 overflow-x-auto p-0 pb-1 [scrollbar-width:none] sm:flex-wrap"
    >
      {SUGGESTED_QUESTIONS.map((q) => (
        <li key={q} className="shrink-0">
          <button
            type="button"
            disabled={disabled}
            onClick={() => onPick(q)}
            className="inline-flex min-h-touch cursor-pointer items-center rounded-full border border-line bg-surface px-4 text-sm font-semibold text-ink transition-colors hover:border-accent hover:bg-accent-tint disabled:cursor-not-allowed disabled:opacity-60"
          >
            {q}
          </button>
        </li>
      ))}
    </ul>
  );
}
