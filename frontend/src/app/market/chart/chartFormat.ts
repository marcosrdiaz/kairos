import type { HistoryPeriod, PortfolioHistoryOut } from "../../../api/generated/schema";
import { formatEur } from "../../../lib/format";

const LOCALE = "es-ES";

export const PERIODS: { value: HistoryPeriod; label: string; name: string }[] = [
  { value: "1w", label: "1S", name: "Última semana" },
  { value: "1m", label: "1M", name: "Último mes" },
  { value: "6m", label: "6M", name: "Últimos 6 meses" },
  { value: "1y", label: "1A", name: "Último año" },
  { value: "max", label: "Todo", name: "Todo el historial" },
];

export const DEFAULT_PERIOD: HistoryPeriod = "1y";

/**
 * Punto de la serie listo para la gráfica: `value` solo sirve para dibujar; los textos salen de
 * los strings del backend (`raw`, `change`, `pct`, `flows`), nunca de cuentas en el navegador.
 */
export interface ChartRow {
  date: string;
  value: number;
  raw: string;
  change: string | null;
  pct: string | null;
  flows: string;
  /** Entró o salió dinero entre este cierre y el anterior (compra, DCA, venta). */
  hasFlow: boolean;
}

const isZero = (v: string) => /^[+-]?0*(\.0*)?$/.test(v.trim());

export function toRows(history: PortfolioHistoryOut): ChartRow[] {
  return history.points.map((p) => ({
    date: p.date,
    value: Number(p.value_eur),
    raw: p.value_eur,
    change: p.change_eur ?? null,
    pct: p.change_pct ?? null,
    flows: p.flows_eur,
    hasFlow: !isZero(p.flows_eur),
  }));
}

export type Trend = "up" | "down" | "flat";

/** Sentido de una variación a partir de su string decimal. */
export function trendOf(value: string | null): Trend {
  if (value === null || isZero(value)) return "flat";
  return value.trim().startsWith("-") ? "down" : "up";
}

/** Importe con signo: "+292,55 €", "−285,33 €" (el signo menos tipográfico). */
export function signedEur(value: string): string {
  const v = value.trim();
  const abs = v.replace(/^[+-]/, "");
  if (isZero(v)) return formatEur(abs);
  return `${v.startsWith("-") ? "−" : "+"}${formatEur(abs)}`;
}

// Dos decimales: las variaciones de un día suelen ser de centésimas (0,04 %, no "0,0 %").
const pct2 = new Intl.NumberFormat(LOCALE, {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  roundingMode: "halfEven",
});

/** Fracción con signo y dos decimales: "+0,88 %", "−0,04 %". */
export function signedPct(value: string): string {
  const v = value.trim();
  const abs = v.replace(/^[+-]/, "") as `${number}`;
  const text = pct2.format(abs);
  if (isZero(v)) return text;
  return `${v.startsWith("-") ? "−" : "+"}${text}`;
}

const dayMonth = new Intl.DateTimeFormat(LOCALE, { day: "numeric", month: "short", timeZone: "UTC" });
const weekDay = new Intl.DateTimeFormat(LOCALE, { weekday: "short", day: "numeric", timeZone: "UTC" });
const monthLong = new Intl.DateTimeFormat(LOCALE, { month: "long", year: "numeric", timeZone: "UTC" });
const shortDay = new Intl.DateTimeFormat(LOCALE, {
  day: "numeric",
  month: "short",
  year: "2-digit",
  timeZone: "UTC",
});
const monthYear = new Intl.DateTimeFormat(LOCALE, { month: "short", year: "2-digit", timeZone: "UTC" });
const fullDay = new Intl.DateTimeFormat(LOCALE, {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

/** Etiqueta del eje X: "lun 2" en una semana; "6 oct" hasta 6 meses; "oct 25" desde un año. */
export function tickDate(iso: string, period: HistoryPeriod): string {
  const date = new Date(iso);
  if (period === "1w") return weekDay.format(date);
  return period === "1y" || period === "max" ? monthYear.format(date) : dayMonth.format(date);
}

/** Fecha corta de los tiradores de la escala de tiempo: "6 nov 26". */
export function chipDate(iso: string): string {
  return shortDay.format(new Date(iso));
}

/** Nombre del mes de un punto, para agrupar la tabla: "Noviembre de 2026". */
export function monthOf(iso: string): string {
  const text = monthLong.format(new Date(iso));
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Día de la semana y día del mes para la tabla: "vie 6". */
export function weekdayOf(iso: string): string {
  return weekDay.format(new Date(iso));
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
