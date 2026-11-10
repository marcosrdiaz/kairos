/*
 * Línea con banda de rango: lo observado es una línea; lo estimado, una línea discontinua
 * con una banda `low`–`high` alrededor. Adaptado del `Band` de Bklit UI
 * (https://github.com/bklit/bklit-ui, MIT). Sin animación de entrada, sin sombras.
 * Todo valor que se pinta viene de fuera: este componente no calcula ninguna cifra.
 */
import { useState, type KeyboardEvent, type PointerEvent } from "react";
import { cn } from "../lib/cn";
import { computeBandLayout, nearestIndex, type BandDatum } from "./band-geometry";
import { useElementWidth } from "./useElementWidth";

export interface RangeBandChartProps {
  data: readonly BandDatum[];
  /** Índice del primer punto estimado: hasta él (incluido) la línea es observada. */
  splitIndex: number;
  /** Nombre de cada punto en el eje x, para la lectura y la tabla accesible. */
  formatX: (x: number) => string;
  formatValue: (value: number) => string;
  /** Descripción corta para lectores de pantalla. */
  label: string;
  height?: number;
  className?: string;
}

const PADDING = { top: 12, right: 12, bottom: 12, left: 56 };

export function RangeBandChart({
  data,
  splitIndex,
  formatX,
  formatValue,
  label,
  height = 220,
  className,
}: RangeBandChartProps) {
  const [ref, width] = useElementWidth<HTMLDivElement>(560);
  const [active, setActive] = useState<number | null>(null);
  const layout = computeBandLayout(data, { width, height, padding: PADDING, splitIndex });
  const current = active === null ? undefined : layout.points[active];
  const datum = active === null ? undefined : data[active];

  function move(event: PointerEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    if (rect.width === 0) return;
    setActive(nearestIndex(layout.points, ((event.clientX - rect.left) / rect.width) * width));
  }

  function key(event: KeyboardEvent<HTMLDivElement>) {
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (step === 0) return;
    event.preventDefault();
    setActive((i) => Math.min(data.length - 1, Math.max(0, (i ?? splitIndex) + step)));
  }

  return (
    <div className={cn("w-full", className)}>
      <div
        ref={ref}
        role="group"
        aria-label={`${label}. Usa las flechas izquierda y derecha para recorrer los puntos.`}
        tabIndex={0}
        onKeyDown={key}
        onBlur={() => setActive(null)}
        className="rounded-control"
      >
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          aria-hidden="true"
          onPointerMove={move}
          onPointerLeave={() => setActive(null)}
          className="block touch-pan-y"
        >
          {layout.yTicks.map((tick) => (
            <g key={tick.value}>
              <line x1={PADDING.left} x2={width - PADDING.right} y1={tick.y} y2={tick.y} className="stroke-line" />
              <text x={PADDING.left - 8} y={tick.y} dy="0.32em" textAnchor="end" className="fill-ink-muted text-sm">
                {formatValue(tick.value)}
              </text>
            </g>
          ))}
          <path d={layout.bandPath} className="fill-chart-1/15" />
          <path d={layout.upperPath} fill="none" strokeDasharray="2 4" className="stroke-chart-1" strokeWidth={1} />
          <path d={layout.lowerPath} fill="none" strokeDasharray="2 4" className="stroke-chart-1" strokeWidth={1} />
          <path d={layout.observedPath} fill="none" className="stroke-accent" strokeWidth={2.25} strokeLinecap="round" />
          <path
            d={layout.estimatedPath}
            fill="none"
            strokeDasharray="6 5"
            className="stroke-accent"
            strokeWidth={2.25}
            strokeLinecap="round"
          />
          {current && (
            <g>
              <line x1={current.x} x2={current.x} y1={PADDING.top} y2={height - PADDING.bottom} className="stroke-line-strong" />
              <circle cx={current.x} cy={current.mid} r={4.5} className="fill-surface stroke-accent" strokeWidth={2.25} />
            </g>
          )}
        </svg>
      </div>

      <p aria-live="polite" className="mt-2 min-h-12 text-sm text-ink-muted">
        {datum && active !== null
          ? active > splitIndex
            ? `${formatX(datum.x)} · estimado: entre ${formatValue(datum.low)} y ${formatValue(datum.high)} (centro ${formatValue(datum.mid)})`
            : `${formatX(datum.x)} · observado: ${formatValue(datum.mid)}`
          : "Pasa el cursor por el gráfico para ver cada punto."}
      </p>

      <table className="sr-only">
        <caption>{label}</caption>
        <thead>
          <tr>
            <th scope="col">Punto</th>
            <th scope="col">Tipo</th>
            <th scope="col">Desde</th>
            <th scope="col">Centro</th>
            <th scope="col">Hasta</th>
          </tr>
        </thead>
        <tbody>
          {data.map((d, i) => (
            <tr key={d.x}>
              <th scope="row">{formatX(d.x)}</th>
              <td>{i > splitIndex ? "Estimado" : "Observado"}</td>
              <td>{formatValue(d.low)}</td>
              <td>{formatValue(d.mid)}</td>
              <td>{formatValue(d.high)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
