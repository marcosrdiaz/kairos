/*
 * Sparkline: minigráfico sin ejes para tablas y tarjetas. Adaptado de `sparkline.tsx` de
 * Bklit UI (https://github.com/bklit/bklit-ui, MIT): misma geometría, sin animación de
 * entrada ni barras, y con el resumen en español para lectores de pantalla.
 * El color es `currentColor`: lo decide quien lo usa (por defecto, el oro de la marca).
 */
import { useState, type PointerEvent } from "react";
import { cn } from "../lib/cn";
import {
  areaPath,
  computeDomain,
  computeLayout,
  describeSeries,
  indexAtX,
  linePath,
  uniformPadding,
  type SparklineCurve,
} from "./sparkline-geometry";

export interface SparklineProps {
  values: readonly number[];
  width?: number;
  height?: number;
  /** Rellena el área bajo la línea con un tinte suave. */
  area?: boolean;
  curve?: SparklineCurve;
  /** Formatea los valores del resumen para lectores de pantalla. */
  formatValue?: (value: number) => string;
  /** Avisa del dato bajo el puntero (null al salir). Sirve para mostrar su valor fuera. */
  onActiveChange?: (index: number | null) => void;
  className?: string;
}

const PADDING = uniformPadding(3);

export function Sparkline({
  values,
  width = 120,
  height = 32,
  area = true,
  curve = "monotone",
  formatValue = String,
  onActiveChange,
  className,
}: SparklineProps) {
  const [active, setActive] = useState<number | null>(null);
  const layout = computeLayout(values, {
    width,
    height,
    padding: PADDING,
    domain: computeDomain(values),
  });
  const point = active === null ? undefined : layout.points[active];

  function move(event: PointerEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    if (rect.width === 0) return;
    const x = ((event.clientX - rect.left) / rect.width) * width;
    const next = indexAtX(x, { count: values.length, width, padding: PADDING });
    setActive(next);
    onActiveChange?.(next);
  }

  function leave() {
    setActive(null);
    onActiveChange?.(null);
  }

  return (
    <svg
      role="img"
      aria-label={describeSeries(values, formatValue)}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      onPointerMove={move}
      onPointerLeave={leave}
      className={cn("inline-block touch-pan-y overflow-visible text-accent", className)}
    >
      {area && <path d={areaPath(layout.points, layout.baselineY, curve)} fill="currentColor" fillOpacity={0.12} />}
      <path
        d={linePath(layout.points, curve)}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.75}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {point && Number.isFinite(point.y) && (
        <circle cx={point.x} cy={point.y} r={3.5} className="fill-surface" stroke="currentColor" strokeWidth={1.75} />
      )}
    </svg>
  );
}
