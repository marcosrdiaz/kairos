import { useEffect, useId, useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
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
import { niceScale, pointDate, tickDate, tickEur, type ChartRow } from "./chartFormat";

interface HistoryChartProps {
  rows: ChartRow[];
  period: HistoryPeriod;
  /** Nombre accesible de la gráfica (el lector lo anuncia al entrar con Tab). */
  label: string;
  /** Punto activo (ratón o flechas del teclado); `null` al salir. */
  onActiveChange: (row: ChartRow | null) => void;
  reducedMotion: boolean;
  /** Pantalla estrecha: gráfica más baja, ejes más pequeños. */
  compact: boolean;
}

/**
 * Avisa al padre del punto activo. Va dentro de la gráfica para leer su estado.
 * El hook devuelve un objeto nuevo en cada render: el efecto depende solo de la fecha (un string)
 * para no entrar en un bucle de renders.
 */
function ActivePointReporter({ rows, onChange }: { rows: ChartRow[]; onChange: (row: ChartRow | null) => void }) {
  const points = useActiveTooltipDataPoints<ChartRow>();
  const activeDate = points?.[0]?.date ?? null;
  useEffect(() => {
    onChange(activeDate === null ? null : (rows.find((r) => r.date === activeDate) ?? null));
  }, [activeDate, rows, onChange]);
  return null;
}

/** Tooltip de marca: franja dorada arriba; el valor manda y la fecha va debajo. */
function PointTooltip({ active, payload }: TooltipContentProps<TooltipValueType, string | number>) {
  const row = payload?.[0]?.payload as ChartRow | undefined;
  if (!active || !row) return null;
  return (
    <div className="kchart-tip">
      <div className="px-3.5 py-2.5">
        <p className="m-0 text-base font-semibold tabular-nums text-ink">{formatEur(row.raw)}</p>
        <p className="m-0 text-sm text-ink-muted">{pointDate(row.date)}</p>
      </div>
    </div>
  );
}

/** Punto activo: núcleo dorado con aro del color de la tarjeta y un halo que late. */
function ActiveDot({ cx, cy }: { cx?: number; cy?: number }) {
  if (cx === undefined || cy === undefined) return null;
  return (
    <g>
      <circle className="kchart-pulse" cx={cx} cy={cy} r={14} fill="var(--kairos-color-gold)" />
      <circle cx={cx} cy={cy} r={7} fill="var(--kairos-color-chart-1)" stroke="var(--kairos-color-surface)" strokeWidth={3} />
    </g>
  );
}

/**
 * Línea dorada con resplandor y área en degradado (Recharts, decisión de T2-18).
 * Accesible con teclado: Tab entra en la gráfica y las flechas recorren los puntos
 * (`accessibilityLayer`). Colores de los tokens `--kairos-*`, así que cambia con el tema.
 */
export function HistoryChart({ rows, period, label, onActiveChange, reducedMotion, compact }: HistoryChartProps) {
  const id = useId().replace(/:/g, "");
  const scale = useMemo(() => niceScale(rows.map((r) => r.value), compact ? 4 : 5), [rows, compact]);
  const tick = { fill: "var(--kairos-color-text-muted)", fontSize: compact ? 12 : 14 };
  return (
    <ResponsiveContainer width="100%" height={compact ? 230 : 300}>
      <AreaChart
        data={rows}
        margin={{ top: 16, right: compact ? 12 : 20, bottom: 0, left: compact ? 0 : 4 }}
        accessibilityLayer
        title={label}
      >
        <defs>
          <linearGradient id={`${id}-fill`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--kairos-color-gold)" stopOpacity={0.38} />
            <stop offset="70%" stopColor="var(--kairos-color-gold)" stopOpacity={0.06} />
            <stop offset="100%" stopColor="var(--kairos-color-gold)" stopOpacity={0} />
          </linearGradient>
          <linearGradient id={`${id}-cursor`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--kairos-color-gold)" stopOpacity={0} />
            <stop offset="35%" stopColor="var(--kairos-color-primary)" stopOpacity={0.9} />
            <stop offset="100%" stopColor="var(--kairos-color-gold)" stopOpacity={0} />
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
        <Tooltip
          content={PointTooltip}
          cursor={{ stroke: `url(#${id}-cursor)`, strokeWidth: 2 }}
          isAnimationActive={false}
        />
        <Area
          type="monotone"
          dataKey="value"
          name="Valor de la cartera"
          stroke="var(--kairos-color-chart-1)"
          strokeWidth={2.5}
          strokeLinecap="round"
          fill={`url(#${id}-fill)`}
          className="kchart-line"
          baseValue="dataMin"
          activeDot={ActiveDot}
          dot={false}
          isAnimationActive={!reducedMotion}
          animationDuration={700}
        />
        <ActivePointReporter rows={rows} onChange={onActiveChange} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
