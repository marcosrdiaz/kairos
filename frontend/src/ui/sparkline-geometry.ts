/*
 * Geometría de sparklines. Adaptada de `sparkline-geometry.ts` de Bklit UI
 * (https://github.com/bklit/bklit-ui, licencia MIT). Se conservan el dominio, el
 * layout y las rutas de línea y área; se quitan las barras y las interpolaciones, y el
 * resumen para lectores de pantalla pasa a español.
 * Funciones puras: entrada → salida, sin DOM.
 */
import { area as d3Area, curveLinear, curveMonotoneX, line as d3Line } from "d3-shape";

export type SparklineCurve = "linear" | "monotone";

export interface SparklinePadding {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface SparklinePoint {
  x: number;
  /** NaN si falta el dato. */
  y: number;
  value: number;
}

export interface SparklineLayout {
  points: SparklinePoint[];
  /** Ordenada en píxeles de la base del área (el 0, acotado al dominio). */
  baselineY: number;
  domain: [number, number];
}

const curves = { linear: curveLinear, monotone: curveMonotoneX } as const;

export function uniformPadding(value: number): SparklinePadding {
  return { top: value, right: value, bottom: value, left: value };
}

/** Dominio de valores. Si la serie es plana, la centra en lugar de pegarla a un borde. */
export function computeDomain(
  values: readonly number[],
  options: { includeZero?: boolean; extra?: readonly number[] } = {},
): [number, number] {
  const finite = [...values, ...(options.extra ?? [])].filter(Number.isFinite);
  if (finite.length === 0) return [0, 1];
  let min = Math.min(...finite);
  let max = Math.max(...finite);
  if (options.includeZero) {
    min = Math.min(min, 0);
    max = Math.max(max, 0);
  }
  return min === max ? [min - 1, max + 1] : [min, max];
}

export function computeLayout(
  values: readonly number[],
  options: { width: number; height: number; padding: SparklinePadding; domain: [number, number] },
): SparklineLayout {
  const { width, height, padding, domain } = options;
  const innerWidth = Math.max(0, width - padding.left - padding.right);
  const innerHeight = Math.max(0, height - padding.top - padding.bottom);
  const [d0, d1] = domain;
  const yOf = (value: number) => padding.top + innerHeight - ((value - d0) / (d1 - d0)) * innerHeight;
  const n = values.length;
  const step = n > 1 ? innerWidth / (n - 1) : 0;
  const points = values.map((value, i) => ({
    x: padding.left + (n > 1 ? step * i : innerWidth / 2),
    y: Number.isFinite(value) ? yOf(value) : Number.NaN,
    value,
  }));
  return { points, baselineY: yOf(Math.min(Math.max(0, d0), d1)), domain };
}

const isDefined = (point: SparklinePoint) => Number.isFinite(point.y);

export function linePath(points: readonly SparklinePoint[], curve: SparklineCurve = "monotone"): string {
  return (
    d3Line<SparklinePoint>()
      .defined(isDefined)
      .x((p) => p.x)
      .y((p) => p.y)
      .curve(curves[curve])(points as SparklinePoint[]) ?? ""
  );
}

export function areaPath(
  points: readonly SparklinePoint[],
  baselineY: number,
  curve: SparklineCurve = "monotone",
): string {
  return (
    d3Area<SparklinePoint>()
      .defined(isDefined)
      .x((p) => p.x)
      .y0(baselineY)
      .y1((p) => p.y)
      .curve(curves[curve])(points as SparklinePoint[]) ?? ""
  );
}

/** Índice del dato más cercano a una posición x (en píxeles del gráfico). */
export function indexAtX(
  x: number,
  options: { count: number; width: number; padding: SparklinePadding },
): number | null {
  const { count, width, padding } = options;
  if (count === 0) return null;
  const innerWidth = width - padding.left - padding.right;
  if (innerWidth <= 0 || count === 1) return 0;
  const raw = Math.round(((x - padding.left) / innerWidth) * (count - 1));
  return Math.min(count - 1, Math.max(0, raw));
}

/**
 * Resumen para lector de pantalla: «12 puntos, de 3,1 a 4,2». Sin variación en %: las cifras
 * no se calculan en el cliente (regla 1); si hace falta, la da la API con su `calc_id`.
 */
export function describeSeries(values: readonly number[], format: (n: number) => string): string {
  const finite = values.filter(Number.isFinite);
  const first = finite[0];
  const last = finite.at(-1);
  if (first === undefined || last === undefined) return "Sin datos";
  return `${finite.length} puntos, de ${format(first)} a ${format(last)}`;
}
