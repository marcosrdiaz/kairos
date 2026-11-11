import { cn } from "../lib/cn";

export type StatusMarkState = "idle" | "processing" | "complete" | "error";

const LABELS: Record<Exclude<StatusMarkState, "idle">, string> = {
  processing: "Respuesta en curso",
  complete: "Respuesta lista",
  error: "No se pudo completar",
};

const COLORS: Record<Exclude<StatusMarkState, "idle">, string> = {
  processing: "text-accent",
  complete: "text-tranquilo",
  error: "text-error",
};

export function StatusMark({ state }: { state: StatusMarkState }) {
  if (state === "idle") return null;

  return (
    <span
      data-status={state}
      className={cn("inline-flex items-center gap-2 text-sm font-medium", COLORS[state])}
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
        className={cn("size-4 shrink-0", state === "processing" && "motion-safe:animate-spin")}
      >
        {state === "processing" && (
          <>
            <circle cx="8" cy="8" r="5.75" strokeOpacity="0.28" />
            <path d="M8 2.25a5.75 5.75 0 0 1 5.75 5.75" />
          </>
        )}
        {state === "complete" && <path d="m3.5 8.25 3 3 6-6.5" />}
        {state === "error" && (
          <>
            <circle cx="8" cy="8" r="5.75" />
            <path d="M8 4.75v3.5M8 11.25h.01" />
          </>
        )}
      </svg>
      <span>{LABELS[state]}</span>
    </span>
  );
}
