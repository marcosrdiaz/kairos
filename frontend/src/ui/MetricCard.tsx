/*
 * Tarjeta de una cifra con selector de periodo y comparación con el periodo anterior.
 * Adaptada de «Metric Card» (`metric-card.tsx`) de Kokonut UI
 * (https://github.com/KokonutUI/kokonutui, MIT). Cambios: colores de los tokens (el original
 * usa grises zinc), sin marcadores de eventos ni desglose por segmento, y la variación llega
 * ya formateada (`changeText`): la tarjeta no calcula ninguna cifra.
 */
import { useId, useState } from "react";
import { cn } from "../lib/cn";
import { RollingNumber } from "./RollingNumber";
import { areaPath, computeDomain, computeLayout, linePath, uniformPadding } from "./sparkline-geometry";
import { useElementWidth } from "./useElementWidth";

export interface MetricPeriod {
  id: string;
  label: string;
  value: number;
  series: readonly number[];
  previousSeries: readonly number[];
  /** Variación ya formateada, con su signo (p. ej. «+3,1 %»). */
  changeText: string;
  direction: "up" | "down" | "flat";
}

export interface MetricCardProps {
  label: string;
  periods: readonly MetricPeriod[];
  formatValue: (value: number) => string;
  className?: string;
}

const PADDING = uniformPadding(4);
const ARROW = { up: "▲", down: "▼", flat: "▬" } as const;
const WORD = { up: "sube", down: "baja", flat: "sin cambios" } as const;

function Trend({ period }: { period: MetricPeriod }) {
  const [ref, width] = useElementWidth<HTMLDivElement>(360);
  const height = 96;
  const domain = computeDomain(period.series, { extra: period.previousSeries });
  const options = { width, height, padding: PADDING, domain };
  const current = computeLayout(period.series, options);
  const previous = computeLayout(period.previousSeries, options);
  return (
    <div ref={ref} className="w-full text-accent">
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true" className="block">
        <path d={linePath(previous.points)} fill="none" stroke="currentColor" strokeOpacity={0.45} strokeWidth={1.5} strokeDasharray="4 4" />
        <path d={areaPath(current.points, height - PADDING.bottom)} fill="currentColor" fillOpacity={0.12} />
        <path d={linePath(current.points)} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" />
      </svg>
    </div>
  );
}

export function MetricCard({ label, periods, formatValue, className }: MetricCardProps) {
  const groupId = useId();
  const [activeId, setActiveId] = useState(periods[0]?.id ?? "");
  const period = periods.find((p) => p.id === activeId) ?? periods[0];
  if (!period) return null;

  return (
    <section aria-labelledby={`${groupId}-label`} className={cn("rounded-card border border-line bg-surface p-5", className)}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 id={`${groupId}-label`} className="m-0 text-base font-medium text-ink-muted">
          {label}
        </h3>
        <div role="radiogroup" aria-label="Periodo" className="flex gap-1 rounded-full border border-line bg-surface-muted p-1">
          {periods.map((p) => (
            <button
              key={p.id}
              type="button"
              role="radio"
              aria-checked={p.id === period.id}
              onClick={() => setActiveId(p.id)}
              className={cn(
                "min-h-touch min-w-touch rounded-full px-3 text-sm font-medium transition-colors",
                p.id === period.id ? "bg-accent text-on-accent" : "text-ink-muted hover:text-ink",
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <p className="m-0 mt-2 text-hero leading-tight font-semibold text-ink">
        <RollingNumber value={period.value} format={formatValue} />
      </p>
      <p className="m-0 mt-1 text-base text-ink-muted">
        <span className={cn("font-medium", period.direction === "up" ? "text-trend-up" : "text-trend-down")}>
          <span aria-hidden="true">{ARROW[period.direction]} </span>
          {period.changeText}
          <span className="sr-only"> ({WORD[period.direction]})</span>
        </span>{" "}
        frente al periodo anterior
      </p>

      <div className="mt-4">
        <Trend period={period} />
        <p className="m-0 mt-1 text-sm text-ink-muted">Línea discontinua: periodo anterior.</p>
      </div>
    </section>
  );
}
