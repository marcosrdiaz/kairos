import { memo, useEffect, useId, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  useActiveTooltipDataPoints,
  type TooltipContentProps,
  type TooltipValueType,
} from "recharts";
import type { HistoryPeriod } from "../../../api/generated/schema";
import { formatEur } from "../../../lib/format";
import type { ActivePointStore } from "./activePoint";
import { Change, FlowTag } from "./Change";
import {
  niceScale,
  pointDate,
  seriesSpanDays,
  tickDate,
  tickEur,
  type ChartRow,
} from "./chartFormat";
import { DOWN, DOWN_BG, INFO, REFERENCE, UP } from "./colors";
import { EventMarkerDot } from "./markers/EventMarkerDot";
import { AlertNewsDot } from "./markers/AlertNewsDot";
import type { AlertNewsMarker } from "./markers/useAlertNewsMarkers";
import type { NewsMarkerStore } from "./markers/newsMarkerStore";
import type { MarkerStore } from "./markers/markerStore";
import type { EventMarker } from "./markers/placeMarkers";

// Recharts renders the active point at z-index 1200; chart pins must remain above it.
const MARKER_Z_INDEX = 1201;


/** Posición (0 arriba, 1 abajo) de `value` dentro de [`low`, `high`], acotada. */
function offsetIn(value: number, high: number, low: number): number {
  if (high === low) return value >= high ? 0 : 1;
  return Math.min(1, Math.max(0, (high - value) / (high - low)));
}

interface HistoryChartProps {
  rows: ChartRow[];
  period: HistoryPeriod;
  /** Valor al empezar el periodo: la línea es verde por encima y granate por debajo. */
  startValue: number;
  /** Nombre accesible de la gráfica (el lector lo anuncia al entrar con Tab). */
  label: string;
  store: ActivePointStore;
  reducedMotion: boolean;
  /** Pantalla estrecha: gráfica más baja, ejes más pequeños. */
  compact: boolean;
  /** Ocupa todo el alto del contenedor (Inicio en escritorio) en vez de una altura fija. */
  fill?: boolean;
  /** Noticias del periodo (T2-22), con su almacén y el id de la tarjeta que las describe. */
  markers?: EventMarker[];
  /** Piso de cada marcador (por `event_id`) para que los cercanos no se pisen. */
  markerLevels?: Map<string, number>;
  markerStore?: MarkerStore;
  markerCardId?: string;
  newsMarkers?: AlertNewsMarker[];
  newsMarkerStore?: NewsMarkerStore;
  newsCardId?: string;
}

/** Lleva el punto activo al almacén. El efecto depende solo de la fecha (string estable). */
function ActivePointReporter({ rows, store }: { rows: ChartRow[]; store: ActivePointStore }) {
  const points = useActiveTooltipDataPoints<ChartRow>();
  const activeDate = points?.[0]?.date ?? null;
  useEffect(() => {
    store.set(activeDate === null ? null : (rows.find((r) => r.date === activeDate) ?? null));
  }, [activeDate, rows, store]);
  return null;
}

/** Tooltip: valor, fecha, variación respecto al cierre anterior y, si la hubo, la aportación. */
function PointTooltip({ active, payload }: TooltipContentProps<TooltipValueType, string | number>) {
  const row = payload?.[0]?.payload as ChartRow | undefined;
  if (!active || !row) return null;
  return (
    <div className="kchart-tip flex flex-col gap-1 px-3.5 py-2.5">
      <p className="m-0 text-base font-semibold tabular-nums text-ink">{formatEur(row.raw)}</p>
      <p className="m-0 text-sm text-ink-muted">{pointDate(row.date)}</p>
      <p className="m-0 text-sm">
        <Change row={row} />
      </p>
      <FlowTag row={row} />
    </div>
  );
}

/**
 * Valor de la cartera: línea verde por encima del valor inicial y granate por debajo, áreas
 * rellenas hasta la referencia dorada (el valor inicial) y puntos azules donde entró o salió
 * dinero (Recharts,
 * decisión de T2-18). Accesible con teclado (`accessibilityLayer`). Memoizada: al mover el ratón
 * no se vuelve a renderizar desde fuera; el punto activo va por el almacén.
 */
export const HistoryChart = memo(function HistoryChart({
  rows,
  period,
  startValue,
  label,
  store,
  reducedMotion,
  compact,
  fill = false,
  markers = [],
  markerLevels,
  markerStore,
  markerCardId = "",
  newsMarkers = [],
  newsMarkerStore,
  newsCardId = "",
}: HistoryChartProps) {
  const id = useId().replace(/:/g, "");
  const values = useMemo(() => rows.map((r) => r.value), [rows]);
  const scale = useMemo(() => niceScale([...values, startValue], compact ? 4 : 5), [values, startValue, compact]);
  const spanDays = seriesSpanDays(rows);
  const flowRows = useMemo(() => rows.filter((r) => r.hasFlow), [rows]);
  // La animación de entrada solo al montar: al arrastrar la escala de tiempo, sin animar.
  const [animate, setAnimate] = useState(!reducedMotion);
  useEffect(() => {
    const t = window.setTimeout(() => setAnimate(false), 800);
    return () => window.clearTimeout(t);
  }, []);
  // Cortes de los degradados en el valor inicial. La caja del trazo va del máximo al mínimo de
  // la serie; la del área, como se rellena hasta la línea de referencia, también la incluye.
  const max = Math.max(...values);
  const min = Math.min(...values);
  const split = offsetIn(startValue, max, min);
  const fillSplit = offsetIn(startValue, Math.max(max, startValue), Math.min(min, startValue));
  const tick = { fill: "var(--kairos-color-text-muted)", fontSize: compact ? 12 : 14 };

  const ActiveDot = ({ cx, cy, payload }: { cx?: number; cy?: number; payload?: ChartRow }) => {
    if (cx === undefined || cy === undefined) return null;
    const color = payload && payload.value < startValue ? DOWN : UP;
    return (
      <g>
        <circle className="kchart-pulse" cx={cx} cy={cy} r={13} fill={color} opacity={0.35} />
        <circle cx={cx} cy={cy} r={6} fill={color} stroke="var(--kairos-color-surface)" strokeWidth={2.5} />
      </g>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={fill ? "100%" : compact ? 230 : 300} debounce={50}>
      <AreaChart
        data={rows}
        // Con noticias, más margen arriba: el círculo del marcador va por encima del punto.
        margin={{
          top: markers.length > 0
            ? 44 + 30 * Math.max(0, ...(markerLevels?.values() ?? []))
            : newsMarkers.length > 0 ? 36 : 16,
          right: compact ? 12 : 20,
          bottom: 0,
          left: compact ? 0 : 4,
        }}
        accessibilityLayer
        aria-label={label}
      >
        <defs>
          <linearGradient id={`${id}-stroke`} x1="0" y1="0" x2="0" y2="1">
            <stop offset={0} stopColor={UP} />
            <stop offset={split} stopColor={UP} />
            <stop offset={split} stopColor={DOWN} />
            <stop offset={1} stopColor={DOWN} />
          </linearGradient>
          {/* Ganancia: verde intenso junto a la línea que se difumina hacia la referencia; pérdida,
              granate de fondo que se intensifica al alejarse de ella. */}
          <linearGradient id={`${id}-fill`} x1="0" y1="0" x2="0" y2="1">
            <stop offset={0} stopColor={UP} stopOpacity={0.34} />
            <stop offset={fillSplit} stopColor={UP} stopOpacity={0.06} />
            <stop offset={fillSplit} stopColor={DOWN_BG} stopOpacity={0.35} />
            <stop offset={1} stopColor={DOWN_BG} stopOpacity={1} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke="var(--kairos-color-border)" strokeDasharray="2 6" />
        <XAxis
          dataKey="date"
          tickFormatter={(iso: string) => tickDate(iso, period, spanDays)}
          tick={tick}
          tickLine={false}
          axisLine={false}
          tickMargin={10}
          minTickGap={compact ? 20 : 36}
        />
        <YAxis
          domain={scale.domain}
          ticks={scale.ticks}
          tickFormatter={tickEur}
          tick={tick}
          tickLine={false}
          axisLine={false}
          width={compact ? 60 : 84}
        />
        <ReferenceLine y={startValue} stroke={REFERENCE} strokeDasharray="6 5" strokeWidth={1.5} />
        <Tooltip
          content={PointTooltip}
          cursor={{ stroke: "var(--kairos-color-border-strong)", strokeWidth: 1.5, strokeDasharray: "3 4" }}
          isAnimationActive={false}
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke={`url(#${id}-stroke)`}
          strokeWidth={2.5}
          strokeLinecap="round"
          fill={`url(#${id}-fill)`}
          baseValue={startValue}
          activeDot={ActiveDot}
          dot={false}
          isAnimationActive={animate}
          animationDuration={600}
        />
        {flowRows.map((r) => (
          <ReferenceDot
            key={r.date}
            x={r.date}
            y={r.value}
            r={5}
            fill={INFO}
            stroke="var(--kairos-color-surface)"
            strokeWidth={2}
          />
        ))}
        {markerStore &&
          markers.map((m) => (
            <ReferenceDot
              key={m.event.event_id}
              x={m.date}
              y={m.value}
              zIndex={MARKER_Z_INDEX}
              shape={(p: { cx?: number; cy?: number }) => (
                <EventMarkerDot
                  cx={p.cx}
                  cy={p.cy}
                  marker={m}
                  level={markerLevels?.get(m.event.event_id) ?? 0}
                  store={markerStore}
                  cardId={markerCardId}
                />
              )}
            />
          ))}
        {newsMarkerStore && newsMarkers.map((m) => (
          <ReferenceDot
            key={m.news.id}
            x={m.date}
            y={m.value}
            zIndex={MARKER_Z_INDEX}
            shape={(p: { cx?: number; cy?: number }) => (
              <AlertNewsDot cx={p.cx} cy={p.cy} marker={m} store={newsMarkerStore} cardId={newsCardId} />
            )}
          />
        ))}
        <ActivePointReporter rows={rows} store={store} />
      </AreaChart>
    </ResponsiveContainer>
  );
});
