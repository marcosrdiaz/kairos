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
import { niceScale, pointDate, tickDate, tickEur, type ChartRow } from "./chartFormat";
import { DOWN, INFO, REFERENCE, UP } from "./colors";


/** Posición (0 arriba, 1 abajo) de `value` dentro de [`low`, `high`], acotada. */
function offsetIn(value: number, high: number, low: number): number {
  if (high === low) return value >= high ? 0 : 1;
  return Math.min(1, Math.max(0, (high - value) / (high - low)));
}

interface HistoryChartProps {
  rows: ChartRow[];
  period: HistoryPeriod;
  /** Valor al empezar el periodo: la línea es verde por encima y naranja por debajo. */
  startValue: number;
  /** Nombre accesible de la gráfica (el lector lo anuncia al entrar con Tab). */
  label: string;
  store: ActivePointStore;
  reducedMotion: boolean;
  /** Pantalla estrecha: gráfica más baja, ejes más pequeños. */
  compact: boolean;
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
 * Valor de la cartera: línea verde por encima del valor inicial y naranja por debajo, áreas
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
}: HistoryChartProps) {
  const id = useId().replace(/:/g, "");
  const values = useMemo(() => rows.map((r) => r.value), [rows]);
  const scale = useMemo(() => niceScale([...values, startValue], compact ? 4 : 5), [values, startValue, compact]);
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
    <ResponsiveContainer width="100%" height={compact ? 230 : 300} debounce={50}>
      <AreaChart
        data={rows}
        margin={{ top: 16, right: compact ? 12 : 20, bottom: 0, left: compact ? 0 : 4 }}
        accessibilityLayer
        title={label}
      >
        <defs>
          <linearGradient id={`${id}-stroke`} x1="0" y1="0" x2="0" y2="1">
            <stop offset={0} stopColor={UP} />
            <stop offset={split} stopColor={UP} />
            <stop offset={split} stopColor={DOWN} />
            <stop offset={1} stopColor={DOWN} />
          </linearGradient>
          {/* Ganancia: verde intenso junto a la línea que se difumina hacia la referencia; pérdida,
              naranja que se intensifica al alejarse de ella. */}
          <linearGradient id={`${id}-fill`} x1="0" y1="0" x2="0" y2="1">
            <stop offset={0} stopColor={UP} stopOpacity={0.34} />
            <stop offset={fillSplit} stopColor={UP} stopOpacity={0.06} />
            <stop offset={fillSplit} stopColor={DOWN} stopOpacity={0.06} />
            <stop offset={1} stopColor={DOWN} stopOpacity={0.34} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke="var(--kairos-color-border)" strokeDasharray="2 6" />
        <XAxis
          dataKey="date"
          tickFormatter={(iso: string) => tickDate(iso, period)}
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
          name="Valor de la cartera"
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
        <ActivePointReporter rows={rows} store={store} />
      </AreaChart>
    </ResponsiveContainer>
  );
});
