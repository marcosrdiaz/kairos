/*
 * Geometría de una línea con banda de rango. Inspirada en `band-geometry.ts` de Bklit UI
 * (https://github.com/bklit/bklit-ui, MIT): el área entre un borde superior y uno inferior,
 * con la línea central encima. Se quitan la animación de morphing y el desvanecido de bordes.
 * Pensada para pintar `low_eur`–`high_eur` (regla de producto 5: rangos, no cifras exactas).
 * Funciones puras: entrada → salida, sin DOM.
 */
import { scaleLinear } from "d3-scale";
import { area as d3Area, curveMonotoneX, line as d3Line } from "d3-shape";

export interface BandDatum {
  /** Posición en el eje x (índice o marca de tiempo). */
  x: number;
  mid: number;
  low: number;
  high: number;
}

export interface BandPadding {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface BandPoint {
  x: number;
  mid: number;
  low: number;
  high: number;
}

export interface BandLayout {
  points: BandPoint[];
  bandPath: string;
  upperPath: string;
  lowerPath: string;
  /** Línea central del tramo observado (hasta `splitIndex`, incluido). */
  observedPath: string;
  /** Línea central del tramo estimado (desde `splitIndex`, incluido). */
  estimatedPath: string;
  /** Valores de los ticks del eje y, de menor a mayor, con su ordenada en píxeles. */
  yTicks: { value: number; y: number }[];
}

export function computeBandLayout(
  data: readonly BandDatum[],
  options: { width: number; height: number; padding: BandPadding; splitIndex: number },
): BandLayout {
  const { width, height, padding, splitIndex } = options;
  const lows = data.map((d) => Math.min(d.low, d.mid));
  const highs = data.map((d) => Math.max(d.high, d.mid));
  const min = lows.length ? Math.min(...lows) : 0;
  const max = highs.length ? Math.max(...highs) : 1;
  const margin = (max - min || 1) * 0.08;
  const xs = data.map((d) => d.x);
  const x = scaleLinear()
    .domain([xs.length ? Math.min(...xs) : 0, xs.length ? Math.max(...xs) : 1])
    .range([padding.left, width - padding.right]);
  const y = scaleLinear()
    .domain([min - margin, max + margin])
    .range([height - padding.bottom, padding.top]);

  const points = data.map((d) => ({ x: x(d.x), mid: y(d.mid), low: y(d.low), high: y(d.high) }));
  const bandPath =
    d3Area<BandPoint>()
      .x((p) => p.x)
      .y0((p) => p.low)
      .y1((p) => p.high)
      .curve(curveMonotoneX)(points) ?? "";
  const edge = (key: "low" | "high") =>
    d3Line<BandPoint>()
      .x((p) => p.x)
      .y((p) => p[key])
      .curve(curveMonotoneX)(points) ?? "";
  const mid = d3Line<BandPoint>()
    .x((p) => p.x)
    .y((p) => p.mid)
    .curve(curveMonotoneX);
  const split = Math.min(Math.max(splitIndex, 0), points.length - 1);

  return {
    points,
    bandPath,
    upperPath: edge("high"),
    lowerPath: edge("low"),
    observedPath: mid(points.slice(0, split + 1)) ?? "",
    estimatedPath: mid(points.slice(split)) ?? "",
    yTicks: y.ticks(3).map((value) => ({ value, y: y(value) })),
  };
}

/** Índice del dato más cercano a una posición x en píxeles. */
export function nearestIndex(points: readonly BandPoint[], px: number): number | null {
  let best: number | null = null;
  let bestDistance = Number.POSITIVE_INFINITY;
  points.forEach((point, i) => {
    const distance = Math.abs(point.x - px);
    if (distance < bestDistance) {
      best = i;
      bestDistance = distance;
    }
  });
  return best;
}
