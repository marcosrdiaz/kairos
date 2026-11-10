import { useEffect, useId, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Brush,
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

/** Desde cuántos puntos se ofrece la barra para acotar el rango (zoom). */
const BRUSH_MIN_POINTS = 40;

interface HistoryChartProps {
  rows: ChartRow[];
  period: HistoryPeriod;
  /** Nombre accesible de la gráfica (el lector lo anuncia al entrar con Tab). */
  label: string;
  /** Punto activo (ratón o flechas del teclado); `null` al salir. */
  onActiveChange: (row: ChartRow | null) => void;
  reducedMotion: boolean;
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

/** Tooltip: el valor manda; la fecha va debajo, en texto secundario. */
function PointTooltip({ active, payload }: TooltipContentProps<TooltipValueType, string | number>) {
  const row = payload?.[0]?.payload as ChartRow | undefined;
  if (!active || !row) return null;
  return (
    <div className="rounded-control border border-line bg-surface px-3 py-2 shadow-none">
      <p className="m-0 text-base font-semibold tabular-nums text-ink">{formatEur(row.raw)}</p>
      <p className="m-0 text-sm text-ink-muted">{pointDate(row.date)}</p>
    </div>
  );
}

/**
 * Línea con área suave del valor de la cartera (Recharts, decisión de T2-18).
 * Accesible con teclado: Tab entra en la gráfica y las flechas recorren los puntos
 * (`accessibilityLayer`). Colores de los tokens `--kairos-*`, así que cambia con el tema.
 */
export function HistoryChart({ rows, period, label, onActiveChange, reducedMotion }: HistoryChartProps) {
  const gradientId = useId();
  const showBrush = rows.length >= BRUSH_MIN_POINTS;
  const scale = useMemo(() => niceScale(rows.map((r) => r.value)), [rows]);
  // Rango visible del Brush, para darle a sus dos tiradores un nombre en español con fechas.
  const [range, setRange] = useState({ start: 0, end: rows.length - 1 });
  const from = rows[range.start]?.date;
  const to = rows[range.end]?.date;
  const brushLabel =
    from && to
      ? `Rango visible: del ${pointDate(from)} al ${pointDate(to)}. Usa las flechas para moverlo.`
      : "Rango visible de la gráfica";
  return (
    <ResponsiveContainer width="100%" height={showBrush ? 320 : 280}>
      <AreaChart
        data={rows}
        margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
        accessibilityLayer
        title={label}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--kairos-color-chart-1)" stopOpacity={0.22} />
            <stop offset="100%" stopColor="var(--kairos-color-chart-1)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke="var(--kairos-color-border)" />
        <XAxis
          dataKey="date"
          tickFormatter={(iso: string) => tickDate(iso, period)}
          tick={{ fill: "var(--kairos-color-text-muted)", fontSize: 14 }}
          tickLine={false}
          axisLine={{ stroke: "var(--kairos-color-border)" }}
          minTickGap={32}
        />
        <YAxis
          domain={scale.domain}
          ticks={scale.ticks}
          tickFormatter={tickEur}
          tick={{ fill: "var(--kairos-color-text-muted)", fontSize: 14 }}
          tickLine={false}
          axisLine={false}
          width={84}
        />
        <Tooltip
          content={PointTooltip}
          cursor={{ stroke: "var(--kairos-color-text-muted)", strokeWidth: 1, strokeDasharray: "4 4" }}
          isAnimationActive={false}
        />
        <Area
          type="monotone"
          dataKey="value"
          name="Valor de la cartera"
          stroke="var(--kairos-color-chart-1)"
          strokeWidth={2}
          fill={`url(#${gradientId})`}
          baseValue="dataMin"
          activeDot={{ r: 6, stroke: "var(--kairos-color-surface)", strokeWidth: 2 }}
          dot={false}
          isAnimationActive={!reducedMotion}
        />
        {showBrush && (
          <Brush
            dataKey="date"
            height={32}
            travellerWidth={12}
            stroke="var(--kairos-color-chart-1)"
            fill="var(--kairos-color-surface)"
            tickFormatter={(iso: string) => tickDate(iso, period)}
            ariaLabel={brushLabel}
            onChange={({ startIndex, endIndex }) => setRange({ start: startIndex, end: endIndex })}
          />
        )}
        <ActivePointReporter rows={rows} onChange={onActiveChange} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
