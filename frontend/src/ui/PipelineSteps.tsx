/*
 * Pasos de un proceso (hecho · en curso · pendiente). Adaptado de la línea de pasos de
 * «Currency Transfer» (`currency-transfer.tsx`) de Kokonut UI
 * (https://github.com/KokonutUI/kokonutui, MIT). Cambios: es controlado (`current`) y no
 * avanza solo, sin importes, bancos ni referencias, y sin iconos de lucide.
 * Cada paso lleva siempre una palabra además del marcador («Hecho», «En curso», «Pendiente»).
 */
import { cn } from "../lib/cn";

export interface PipelineStep {
  id: string;
  title: string;
  detail?: string;
}

export interface PipelineStepsProps {
  steps: readonly PipelineStep[];
  /** Índice del paso en curso. `steps.length` significa que todos están hechos. */
  current: number;
  label: string;
  className?: string;
}

function Marker({ state }: { state: "done" | "current" | "pending" }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "relative z-10 flex size-7 shrink-0 items-center justify-center rounded-full border-2",
        state === "done" && "border-accent bg-accent text-on-accent",
        state === "current" && "border-accent bg-accent-tint text-accent",
        state === "pending" && "border-line-strong bg-surface text-ink-muted",
      )}
    >
      {state === "done" ? (
        <svg viewBox="0 0 16 16" className="size-3.5" fill="none" stroke="currentColor" strokeWidth={2.5}>
          <path d="M3.5 8.5l3 3 6-7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : (
        <span className={cn("size-2 rounded-full", state === "current" ? "bg-accent" : "bg-line-strong")} />
      )}
    </span>
  );
}

const WORDS = { done: "Hecho", current: "En curso", pending: "Pendiente" } as const;

export function PipelineSteps({ steps, current, label, className }: PipelineStepsProps) {
  return (
    <ol aria-label={label} className={cn("m-0 list-none p-0", className)}>
      {steps.map((step, i) => {
        const state = i < current ? "done" : i === current ? "current" : "pending";
        const last = i === steps.length - 1;
        return (
          <li key={step.id} aria-current={state === "current" ? "step" : undefined} className="relative flex gap-4 pb-6 last:pb-0">
            {!last && (
              <span
                aria-hidden="true"
                className={cn("absolute top-7 bottom-0 left-3.5 w-0.5 -translate-x-1/2", state === "done" ? "bg-accent" : "bg-line")}
              />
            )}
            <Marker state={state} />
            <div className="min-w-0 pt-0.5">
              <p className="m-0 text-base font-medium text-ink">
                {step.title} <span className="ml-1 text-sm font-normal text-ink-muted">· {WORDS[state]}</span>
              </p>
              {step.detail && <p className="m-0 text-sm text-ink-muted">{step.detail}</p>}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
