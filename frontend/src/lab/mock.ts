/*
 * Datos de ejemplo del laboratorio. TODOS son ilustrativos ("illustrative": true): series
 * inventadas en unidades abstractas («u.»), sin relación con el motor de impacto ni con las
 * carteras de Laura y Javier. No los uses fuera de /lab.
 */
import type { BandDatum } from "../ui/band-geometry";
import type { MetricPeriod } from "../ui/MetricCard";
import type { DayState, SourceStatus } from "../ui/UptimeCard";

export const ILLUSTRATIVE = true;

const unit = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 0 });
export const formatUnits = (value: number) => `${unit.format(value)} u.`;

/** Serie observada (los 6 primeros puntos, sin rango) y estimada (rango que se abre). */
export const BAND_DATA: BandDatum[] = [
  { x: 0, mid: 100, low: 100, high: 100 },
  { x: 1, mid: 104, low: 104, high: 104 },
  { x: 2, mid: 101, low: 101, high: 101 },
  { x: 3, mid: 107, low: 107, high: 107 },
  { x: 4, mid: 110, low: 110, high: 110 },
  { x: 5, mid: 108, low: 108, high: 108 },
  { x: 6, mid: 112, low: 106, high: 118 },
  { x: 7, mid: 115, low: 105, high: 125 },
  { x: 8, mid: 117, low: 103, high: 131 },
  { x: 9, mid: 121, low: 102, high: 140 },
];
export const BAND_SPLIT = 5;
export const bandLabel = (x: number) => (x <= BAND_SPLIT ? `Mes ${x + 1}` : `Mes ${x + 1} (estimado)`);

export const SPARKLINES: { name: string; values: number[] }[] = [
  { name: "Serie A", values: [10, 12, 11, 14, 13, 16, 15, 18, 17, 20] },
  { name: "Serie B", values: [20, 19, 21, 18, 17, 18, 16, 15, 16, 14] },
  { name: "Serie C", values: [12, 12, 13, 12, 12, 13, 13, 12, 13, 13] },
  { name: "Serie D", values: [8, 11, 9, 14, 10, 15, 11, 16, 12, 17] },
];

function wave(length: number, base: number, amplitude: number, phase: number): number[] {
  return Array.from({ length }, (_, i) => Math.round(base + amplitude * Math.sin(i / 3 + phase) + i * 0.6));
}

export const METRIC_PERIODS: MetricPeriod[] = [
  {
    id: "7",
    label: "7 d",
    value: 1200,
    series: wave(7, 40, 6, 0),
    previousSeries: wave(7, 38, 5, 1),
    changeText: "+3 %",
    direction: "up",
  },
  {
    id: "30",
    label: "30 d",
    value: 4850,
    series: wave(30, 40, 8, 0.5),
    previousSeries: wave(30, 42, 7, 2),
    changeText: "-2 %",
    direction: "down",
  },
  {
    id: "90",
    label: "90 d",
    value: 14300,
    series: wave(45, 36, 9, 1),
    previousSeries: wave(45, 36, 8, 1),
    changeText: "0 %",
    direction: "flat",
  },
];

const day = (pattern: string): DayState[] =>
  [...pattern].map((c) => (c === "o" ? "ok" : c === "l" ? "late" : "none"));

export const SOURCES: SourceStatus[] = [
  { name: "Fuente de ejemplo 1", days: day("oooooooooooooooolooooooooooooo") },
  { name: "Fuente de ejemplo 2", days: day("oooooooooooooloollooooooooooooo".slice(0, 30)) },
  { name: "Fuente de ejemplo 3", days: day("nnnnnnnnnnoooooooooooooooooooo") },
];

export const HEADLINES = ["Todo en calma", "Conviene mirar un par de cosas", "Revisa tu plan"];
