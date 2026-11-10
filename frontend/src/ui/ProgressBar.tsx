/*
 * Barra de progreso determinada. Adaptada de `halo-progress.tsx` de Cult UI
 * (https://github.com/nolly-studio/cult-ui, MIT). Del original solo queda el relleno con
 * `scaleX` y muelle (una transformación, no `width`). Se quitan el brillo con degradado
 * multicolor, el cristal esmerilado, las sombras interiores, la barra indeterminada y la
 * dependencia de Base UI: DESIGN.md pide un sistema plano, sin sombras.
 * `target` marca una referencia (por ejemplo, lo previsto por el plan del usuario).
 */
import { useId } from "react";
import { motion, useReducedMotion } from "motion/react";
import { cn } from "../lib/cn";

export interface ProgressBarProps {
  value: number;
  max?: number;
  label: string;
  /** Texto de la lectura (p. ej. «3 de 4 aportaciones»). Lo anuncia el lector de pantalla. */
  valueText: string;
  /** Posición de la referencia, en la misma escala que `value`. */
  target?: number;
  targetLabel?: string;
  className?: string;
}

const clamp = (n: number) => Math.min(1, Math.max(0, n));

export function ProgressBar({ value, max = 100, label, valueText, target, targetLabel, className }: ProgressBarProps) {
  const labelId = useId();
  const reduceMotion = useReducedMotion();
  const fraction = max > 0 ? clamp(value / max) : 0;
  const targetFraction = target === undefined || max <= 0 ? null : clamp(target / max);

  return (
    <div className={cn("w-full", className)}>
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <span id={labelId} className="text-sm font-medium text-ink">
          {label}
        </span>
        <span className="text-sm tabular-nums text-ink-muted">{valueText}</span>
      </div>
      <div
        role="progressbar"
        aria-labelledby={labelId}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={Math.min(Math.max(value, 0), max)}
        aria-valuetext={valueText}
        className="relative h-3 w-full rounded-full border border-line-strong bg-surface-muted"
      >
        <div className="absolute inset-0 overflow-hidden rounded-full">
          <motion.div
            initial={false}
            animate={{ scaleX: fraction }}
            transition={reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 160, damping: 28 }}
            className="h-full w-full origin-left bg-accent"
          />
        </div>
        {targetFraction !== null && (
          <span
            title={targetLabel}
            style={{ left: `${targetFraction * 100}%` }}
            className="absolute -top-1 h-5 w-0.5 -translate-x-1/2 bg-ink"
          />
        )}
      </div>
      {targetFraction !== null && targetLabel && <p className="mt-1.5 text-sm text-ink-muted">{targetLabel}</p>}
    </div>
  );
}
