import { useCallback, useMemo, useState, useSyncExternalStore } from "react";
import type { HistoryPeriod, PortfolioHistoryOut } from "../../../api/generated/schema";
import { usePortfolioHistory } from "../../../api/hooks/usePortfolioHistory";
import { EmptyNote } from "../../../components/PageTitle";
import { TraceFigure } from "../../../components/trace/TraceFigure";
import { formatEur } from "../../../lib/format";
import "./chart.css";
import { ChartBackdrop } from "./ChartBackdrop";
import { DEFAULT_PERIOD, PERIODS, pointDate, toRows, type ChartRow } from "./chartFormat";
import { HistoryChart } from "./HistoryChart";
import { HistoryTable } from "./HistoryTable";
import { PeriodPicker } from "./PeriodPicker";
import { RangeSelector } from "./RangeSelector";

/** Desde cuántos puntos se ofrece la escala de tiempo para acotar el rango. */
const RANGE_MIN_POINTS = 10;
const COMPACT = "(max-width: 39.999rem)";

function prefersReducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Pantalla estrecha (móvil): gráfica más baja y ejes más pequeños. */
function useCompact(): boolean {
  return useSyncExternalStore(
    (notify) => {
      if (typeof window.matchMedia !== "function") return () => undefined;
      const query = window.matchMedia(COMPACT);
      query.addEventListener("change", notify);
      return () => query.removeEventListener("change", notify);
    },
    () => typeof window.matchMedia === "function" && window.matchMedia(COMPACT).matches,
  );
}

/** Aportaciones o retiradas del periodo, para no confundirlas con rentabilidad. */
function FlowsNote({ history }: { history: PortfolioHistoryOut }) {
  const flows = history.net_flows_eur;
  if (Number(flows) === 0) return <>Sin aportaciones ni retiradas en el periodo.</>;
  const amount = flows.startsWith("-") ? flows.slice(1) : flows;
  return (
    <>
      {flows.startsWith("-") ? "Incluye retiradas por " : "Incluye aportaciones por "}
      <TraceFigure calcId={history.calc_id}>{formatEur(amount)}</TraceFigure>.
    </>
  );
}

const DOT = <span className="mx-2 text-(--kairos-color-gold-deep)" aria-hidden="true">·</span>;

/** Valor del punto activo (o del último) en grande y, en una sola línea, fecha, inicio y flujos. */
function Readout({ history, active }: { history: PortfolioHistoryOut; active: ChartRow | null }) {
  const last = history.points[history.points.length - 1];
  const raw = active?.raw ?? last?.value_eur;
  const date = active?.date ?? last?.date;
  if (!raw || !date) return null;
  return (
    <div className="flex flex-col gap-1 px-5 sm:px-6">
      <p className="kchart-value m-0 text-3xl font-semibold tabular-nums sm:text-4xl">
        <TraceFigure calcId={history.calc_id}>{formatEur(raw)}</TraceFigure>
      </p>
      <p className="m-0 text-sm text-ink-muted">
        <span>{active ? pointDate(date) : `Último cierre: ${pointDate(date)}`}</span>
        {DOT}
        <span>
          Al empezar el periodo:{" "}
          <span className="font-semibold tabular-nums text-ink">
            <TraceFigure calcId={history.calc_id}>{formatEur(history.start_value_eur)}</TraceFigure>
          </span>
        </span>
        {DOT}
        <span>
          <FlowsNote history={history} />
        </span>
      </p>
    </div>
  );
}

interface ChartBodyProps {
  history: PortfolioHistoryOut;
  rows: ChartRow[];
  period: HistoryPeriod;
  periodName: string;
}

/** Gráfica, escala de tiempo y tabla. Se monta de nuevo al cambiar de serie (rango completo). */
function ChartBody({ history, rows, period, periodName }: ChartBodyProps) {
  const compact = useCompact();
  const [active, setActive] = useState<ChartRow | null>(null);
  const onActiveChange = useCallback((row: ChartRow | null) => setActive(row), []);
  const [range, setRange] = useState({ start: 0, end: rows.length - 1 });
  const visible = useMemo(() => rows.slice(range.start, range.end + 1), [rows, range]);
  const zoomed = range.start > 0 || range.end < rows.length - 1;
  return (
    <>
      <Readout history={history} active={active} />
      <p className="sr-only" aria-live="polite">
        {active ? `${pointDate(active.date)}: ${formatEur(active.raw)}` : ""}
      </p>
      <div className="pr-1 sm:pr-2">
        <HistoryChart
          rows={visible}
          period={period}
          label={`Valor de la cartera. ${periodName}. Usa las flechas para recorrer los días.`}
          onActiveChange={onActiveChange}
          reducedMotion={prefersReducedMotion()}
          compact={compact}
        />
      </div>
      {rows.length >= RANGE_MIN_POINTS && (
        <div className="flex flex-col gap-2">
          <RangeSelector
            rows={rows}
            start={range.start}
            end={range.end}
            onChange={(start, end) => setRange({ start, end })}
          />
          <div className="flex min-h-touch items-center justify-between gap-3 px-5 sm:px-6">
            <p className="m-0 text-sm text-ink-muted">Arrastra la ventana o sus bordes para acercar la gráfica.</p>
            {zoomed && (
              <button
                type="button"
                onClick={() => setRange({ start: 0, end: rows.length - 1 })}
                className="min-h-touch shrink-0 rounded-full border border-line bg-surface px-4 text-sm font-semibold text-accent hover:bg-accent-tint"
              >
                Ver todo el periodo
              </button>
            )}
          </div>
        </div>
      )}
      <HistoryTable history={history} periodName={periodName} activeDate={active?.date ?? null} />
    </>
  );
}

/**
 * Evolución del valor de la cartera en Inicio (T2-18): selector de periodo, gráfica interactiva
 * (ratón y teclado), escala de tiempo para acercar, punto activo anunciado al lector de pantalla
 * y tabla alternativa. Cifras del backend con `calc_id`; la serie usa precios de cierre, sin el
 * impacto de eventos. Estilos de marca en `chart.css`.
 */
export function PortfolioChart({ portfolioId }: { portfolioId: string }) {
  const [period, setPeriod] = useState<HistoryPeriod>(DEFAULT_PERIOD);
  const { data, isPending, isError, isPlaceholderData } = usePortfolioHistory(portfolioId, period);
  const periodName = PERIODS.find((p) => p.value === period)?.name ?? "";
  // Respuesta sin puntos (o inesperada): estado vacío, nunca una gráfica inventada.
  const hasPoints = Array.isArray(data?.points) && data.points.length > 0;
  // Filas estables entre renders: la gráfica y su efecto de punto activo dependen de ellas.
  const rows = useMemo(() => (data && hasPoints ? toRows(data) : []), [data, hasPoints]);

  return (
    <section aria-labelledby="chart-heading" className="kchart-card flex flex-col gap-4 rounded-card pt-5 sm:pt-6">
      <ChartBackdrop />
      <div className="flex flex-col gap-4 px-5 sm:flex-row sm:items-start sm:justify-between sm:px-6">
        <div>
          <h2 id="chart-heading" className="m-0 mb-1 text-lg font-semibold text-ink">
            Evolución de tu cartera
          </h2>
          <p className="m-0 text-sm text-ink-muted">
            Valor con precios de cierre. No incluye el impacto estimado de los eventos.
          </p>
        </div>
        <PeriodPicker value={period} onChange={setPeriod} />
      </div>

      {isPending && (
        <div role="status" aria-label="Cargando la evolución de tu cartera" className="mx-5 mb-5 h-80 rounded-control bg-surface-muted motion-safe:animate-pulse sm:mx-6" />
      )}
      {isError && !data && (
        <div className="mx-5 mb-5 sm:mx-6">
          <EmptyNote>Ahora mismo no podemos mostrar la evolución de tu cartera. Vuelve a intentarlo en un rato.</EmptyNote>
        </div>
      )}
      {data && !hasPoints && (
        <div className="mx-5 mb-5 sm:mx-6">
          <EmptyNote>Todavía no hay cierres para este periodo.</EmptyNote>
        </div>
      )}
      {data && hasPoints && (
        <div
          aria-busy={isPlaceholderData}
          className={`flex flex-col gap-4 transition-opacity duration-200 ${isPlaceholderData ? "opacity-60" : ""}`}
        >
          <ChartBody key={`${period}-${rows.length}-${data.calc_id}`} history={data} rows={rows} period={period} periodName={periodName} />
        </div>
      )}
    </section>
  );
}
