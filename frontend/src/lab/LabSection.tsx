import type { ReactNode } from "react";
import { cn } from "../lib/cn";

export interface Verdict {
  fits: boolean;
  /** Por qué encaja o choca con DESIGN.md. Obligatorio en los dos casos. */
  reason: string;
}

interface LabSectionProps {
  id: string;
  title: string;
  /** De dónde viene y con qué licencia (p. ej. «Bklit UI · MIT»). */
  origin: string;
  originUrl: string;
  verdict: Verdict;
  /** Qué se ha cambiado respecto al original. */
  changes: string;
  children: ReactNode;
}

export function LabSection({ id, title, origin, originUrl, verdict, changes, children }: LabSectionProps) {
  return (
    <section aria-labelledby={`${id}-title`} className="rounded-card border border-line bg-surface p-5 lg:p-6">
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <h2 id={`${id}-title`} className="m-0 text-xl font-semibold text-ink">
          {title}
        </h2>
        <p
          className={cn(
            "m-0 rounded-full px-3 py-1 text-sm font-medium",
            verdict.fits ? "bg-success-bg text-success" : "bg-warn-bg text-warn",
          )}
        >
          {verdict.fits ? "Encaja con DESIGN.md" : "Choca con DESIGN.md"}
        </p>
      </div>
      <p className="m-0 mt-2 text-base text-ink">{verdict.reason}</p>
      <p className="m-0 mt-1 text-sm text-ink-muted">
        Origen:{" "}
        <a href={originUrl} className="text-accent underline underline-offset-2" target="_blank" rel="noreferrer">
          {origin}
        </a>
        . Cambios: {changes}
      </p>
      <div className="mt-5">{children}</div>
    </section>
  );
}
