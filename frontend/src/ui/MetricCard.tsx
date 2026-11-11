/*
 * Tarjeta de una cifra con selector de periodo. Adaptada de «Metric Card» (`metric-card.tsx`) de
 * Kokonut UI (https://github.com/KokonutUI/kokonutui, MIT). Cambios: colores de los tokens (el
 * original usa grises zinc), sin marcadores de eventos ni desglose por segmento, sin línea del
 * periodo anterior y sin variación calculada. La tarjeta es controlada (el periodo lo guarda
 * quien la usa, que pide los datos de ese periodo) y no formatea ni calcula ninguna cifra: recibe
 * `value` y `detail` ya formateados (envueltos en `Traced` en la app). `series` solo sirve para
 * dibujar la línea.
 */
import { useId, type ReactNode } from "react";
import { cn } from "../lib/cn";
import { areaPath, computeDomain, computeLayout, linePath, uniformPadding } from "./sparkline-geometry";
import { useElementWidth } from "./useElementWidth";

export interface MetricPeriod {
  id: string;
  /** Etiqueta corta del botón («1M»). */
  label: string;
  /** Nombre completo para el lector de pantalla («Último mes»). */
  name?: string;
}

export interface MetricCardProps {
  label: string;
  periods: readonly MetricPeriod[];
  activeId: string;
  onPeriodChange: (id: string) => void;
  /** Cifra principal, ya formateada. */
  value: ReactNode;
  /** Línea bajo la cifra (fecha, contexto). */
  detail?: ReactNode;
  /** Contexto del periodo elegido, ya formateado. */
  periodDetail?: ReactNode;
  /** Valores del periodo, solo para dibujar. Vacío: sin línea. */
  series?: readonly number[];
  /** Descripción de la línea para el lector de pantalla. */
  seriesLabel?: string;
  /** Mientras llega el periodo nuevo se atenúa la línea (la anterior se conserva). */
  busy?: boolean;
  children?: ReactNode;
  className?: string;
}

const PADDING = uniformPadding(4);
const HEIGHT = 96;

function Trend({ series, label, busy }: { series: readonly number[]; label?: string; busy?: boolean }) {
  const [ref, width] = useElementWidth<HTMLDivElement>(360);
  const domain = computeDomain(series);
  const layout = computeLayout(series, { width, height: HEIGHT, padding: PADDING, domain });
  return (
    <div ref={ref} className={cn("w-full text-accent transition-opacity", busy && "opacity-50")}>
      <svg
        width={width}
        height={HEIGHT}
        viewBox={`0 0 ${width} ${HEIGHT}`}
        role={label ? "img" : undefined}
        aria-label={label}
        aria-hidden={label ? undefined : true}
        className="block"
      >
        <path d={areaPath(layout.points, HEIGHT - PADDING.bottom)} fill="currentColor" fillOpacity={0.12} />
        <path d={linePath(layout.points)} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" />
      </svg>
    </div>
  );
}

export function MetricCard({
  label,
  periods,
  activeId,
  onPeriodChange,
  value,
  detail,
  periodDetail,
  series = [],
  seriesLabel,
  busy,
  children,
  className,
}: MetricCardProps) {
  const groupId = useId();
  return (
    <section aria-labelledby={`${groupId}-label`} className={cn("rounded-card border border-line bg-surface p-5", className)}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 id={`${groupId}-label`} className="m-0 text-base font-medium text-ink-muted">
            {label}
          </h3>
          <p className="m-0 mt-1 text-3xl font-semibold leading-tight tabular-nums text-ink">{value}</p>
          {detail && <p className="m-0 mt-1 text-sm text-ink-muted">{detail}</p>}
        </div>
        <fieldset className="m-0 flex gap-1 rounded-full border border-line bg-surface-muted p-1">
          <legend className="sr-only">Periodo</legend>
          {periods.map((p) => (
            <label
              key={p.id}
              className={cn(
                "flex min-h-touch min-w-touch cursor-pointer items-center justify-center rounded-full px-3 text-sm font-medium transition-colors has-focus-visible:outline-3 has-focus-visible:outline-offset-2 has-focus-visible:outline-focus has-focus-visible:outline-solid",
                p.id === activeId ? "bg-accent text-on-accent" : "text-ink-muted hover:text-ink",
              )}
            >
              <input
                type="radio"
                name={`${groupId}-period`}
                value={p.id}
                checked={p.id === activeId}
                onChange={() => onPeriodChange(p.id)}
                aria-label={p.name ?? p.label}
                className="sr-only"
              />
              <span aria-hidden={p.name ? true : undefined}>{p.label}</span>
            </label>
          ))}
        </fieldset>
      </div>

      {series.length > 1 && (
        <div className="mt-4">
          <Trend series={series} label={seriesLabel} busy={busy} />
        </div>
      )}
      {periodDetail && <p className="m-0 mt-2 text-sm text-ink-muted">{periodDetail}</p>}
      {children}
    </section>
  );
}
