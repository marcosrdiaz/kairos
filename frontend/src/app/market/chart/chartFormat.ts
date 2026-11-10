import type { HistoryPeriod, PortfolioHistoryOut } from "../../../api/generated/schema";

const LOCALE = "es-ES";

export const PERIODS: { value: HistoryPeriod; label: string; name: string }[] = [
  { value: "1m", label: "1M", name: "Último mes" },
  { value: "3m", label: "3M", name: "Últimos 3 meses" },
  { value: "6m", label: "6M", name: "Últimos 6 meses" },
  { value: "1y", label: "1A", name: "Último año" },
  { value: "max", label: "Todo", name: "Todo el historial" },
];

export const DEFAULT_PERIOD: HistoryPeriod = "1y";

/** Punto de la serie listo para la gráfica: `value` solo sirve para dibujar; el texto sale de `raw`. */
export interface ChartRow {
  date: string;
  value: number;
  raw: string;
}

export function toRows(history: PortfolioHistoryOut): ChartRow[] {
  return history.points.map((p) => ({ date: p.date, value: Number(p.value_eur), raw: p.value_eur }));
}

const dayMonth = new Intl.DateTimeFormat(LOCALE, { day: "numeric", month: "short", timeZone: "UTC" });
const monthYear = new Intl.DateTimeFormat(LOCALE, { month: "short", year: "2-digit", timeZone: "UTC" });
const fullDay = new Intl.DateTimeFormat(LOCALE, {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

/** Etiqueta del eje X: "6 oct" en periodos cortos; "oct 25" desde un año. */
export function tickDate(iso: string, period: HistoryPeriod): string {
  const date = new Date(iso);
  return period === "1y" || period === "max" ? monthYear.format(date) : dayMonth.format(date);
}

/** Fecha del punto activo y de la tabla: "6 de noviembre de 2026" (el día del cierre, en UTC). */
export function pointDate(iso: string): string {
  return fullDay.format(new Date(iso));
}

const compactEur = new Intl.NumberFormat(LOCALE, {
  style: "currency",
  currency: "EUR",
  notation: "compact",
  maximumFractionDigits: 1,
});

/**
 * Escala del eje Y con divisiones redondas (pasos de 1, 2, 2,5 o 5 por una potencia de 10),
 * unas `target` marcas que cubren todos los valores. Solo geometría: no son cifras del cálculo.
 */
export function niceScale(values: number[], target = 5): { domain: [number, number]; ticks: number[] } {
  if (values.length === 0) return { domain: [0, 1], ticks: [0, 1] };
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || Math.abs(max) || 1;
  const raw = span / target;
  const power = 10 ** Math.floor(Math.log10(raw));
  const step = ([1, 2, 2.5, 5, 10].find((m) => m * power >= raw) ?? 10) * power;
  const low = Math.floor(min / step) * step;
  const high = Math.max(Math.ceil(max / step) * step, low + step);
  const ticks: number[] = [];
  for (let t = low; t <= high + step / 2; t += step) ticks.push(Math.round(t * 100) / 100);
  return { domain: [low, high], ticks };
}

/** Marcas del eje Y ("34,5 mil €"): son divisiones de la escala, no cifras del cálculo. */
export function tickEur(value: number): string {
  return compactEur.format(value);
}
