import { useCallback, useMemo, useState, useSyncExternalStore } from "react";
import type { HistoryPeriod, PortfolioHistoryOut } from "../../../api/generated/schema";
import { usePortfolioHistory } from "../../../api/hooks/usePortfolioHistory";
import { EmptyNote } from "../../../components/PageTitle";
import { formatEur } from "../../../lib/format";
import { createActivePointStore, useActivePoint, type ActivePointStore } from "./activePoint";
import "./chart.css";
import { ChartBackdrop } from "./ChartBackdrop";
import { ChartLegend } from "./ChartLegend";
import { Change } from "./Change";
import { DEFAULT_PERIOD, PERIODS, chipDate, pointDate, signedEur, toRows } from "./chartFormat";
import { HistoryChart } from "./HistoryChart";
import { HistoryTable } from "./HistoryTable";
import { PeriodPicker } from "./PeriodPicker";
import { RangeSelector } from "./RangeSelector";
import { TraceHint } from "./TraceHint";

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

/** Fuentes de la serie en una línea, para las pistas de «de dónde sale». */
function sourceLine(history: PortfolioHistoryOut): string {
  const assets = history.sources.filter((s) => s.kind === "price").length;
  const fx = history.sources.some((s) => s.kind === "fx") ? " y tipo de cambio" : "";
  const last = history.points[history.points.length - 1];
  return `Precios de cierre de ${assets} ${assets === 1 ? "activo" : "activos"}${fx}. Datos a ${last ? chipDate(last.date) : "—"}.`;
}

const DOT = <span className="mx-2 text-ink-muted" aria-hidden="true">·</span>;

/** Valor del punto activo (o del último) en grande y, en una sola línea, fecha, inicio y flujos. */
function Readout({ history, store }: { history: PortfolioHistoryOut; store: ActivePointStore }) {
  const active = useActivePoint(store);
  const lastRow = useMemo(() => toRows(history).at(-1) ?? null, [history]);
  const row = active ?? lastRow;
  if (!row) return null;
  const source = sourceLine(history);
  const flows = history.net_flows_eur;
  const noFlows = Number(flows) === 0;
  return (
    <div className="flex flex-col gap-1 px-5 sm:px-6">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <p className="m-0 text-3xl font-semibold tabular-nums text-ink sm:text-4xl">
          <TraceHint calcId={history.calc_id} text="Valor de tu cartera ese día: participaciones × precio de cierre." source={source}>
            {formatEur(row.raw)}
          </TraceHint>
        </p>
        <span className="text-base">
          <Change row={row} />
        </span>
      </div>
      <p className="m-0 text-sm text-ink-muted">
        <span>{active ? pointDate(row.date) : `Último cierre: ${pointDate(row.date)}`}</span>
        {DOT}
        <span>
          Al empezar el periodo:{" "}
          <span className="font-semibold tabular-nums text-ink">
            <TraceHint calcId={history.calc_id} text="Valor de tu cartera en el primer cierre del periodo." source={source}>
              {formatEur(history.start_value_eur)}
            </TraceHint>
          </span>
        </span>
        {DOT}
        {noFlows ? (
          <span>Sin aportaciones ni retiradas en el periodo.</span>
        ) : (
          <span>
            {flows.startsWith("-") ? "Retiradas: " : "Aportaciones: "}
            <span className="font-semibold tabular-nums text-info">
              <TraceHint calcId={history.calc_id} text="Dinero que entró o salió en el periodo (compras, aportaciones, ventas). No es rentabilidad." source={source}>
                {signedEur(flows)}
              </TraceHint>
            </span>
          </span>
        )}
      </p>
    </div>
  );
}

/** Anuncia el punto activo al lector de pantalla (solo esto se repinta al mover el ratón). */
function LiveActive({ store }: { store: ActivePointStore }) {
  const active = useActivePoint(store);
  return (
    <p className="sr-only" aria-live="polite">
      {active ? `${pointDate(active.date)}: ${formatEur(active.raw)}` : ""}
    </p>
  );
}

interface ChartBodyProps {
  history: PortfolioHistoryOut;
  period: HistoryPeriod;
  periodName: string;
}

/** Gráfica, escala de tiempo y tabla. Se monta de nuevo al cambiar de serie (rango completo). */
function ChartBody({ history, period, periodName }: ChartBodyProps) {
  const compact = useCompact();
  const rows = useMemo(() => toRows(history), [history]);
  const [store] = useState(createActivePointStore);
  const [range, setRange] = useState({ start: 0, end: rows.length - 1 });
  const visible = useMemo(() => rows.slice(range.start, range.end + 1), [rows, range]);
  const onRange = useCallback((start: number, end: number) => setRange({ start, end }), []);
  const zoomed = range.start > 0 || range.end < rows.length - 1;
  const startValue = Number(history.start_value_eur);
  return (
    <>
      <Readout history={history} store={store} />
      <LiveActive store={store} />
      <div className="pr-1 sm:pr-2">
        <HistoryChart
          rows={visible}
          period={period}
          startValue={startValue}
          label={`Valor de la cartera. ${periodName}. Usa las flechas para recorrer los días.`}
          store={store}
          reducedMotion={prefersReducedMotion()}
          compact={compact}
        />
      </div>
      {rows.length >= RANGE_MIN_POINTS && (
        <div className="flex flex-col gap-1">
          <RangeSelector rows={rows} start={range.start} end={range.end} onChange={onRange} />
          {zoomed && (
            <div className="flex justify-end px-5 sm:px-6">
              <button
                type="button"
                onClick={() => onRange(0, rows.length - 1)}
                className="min-h-touch shrink-0 rounded-full border border-line bg-surface px-4 text-sm font-semibold text-accent hover:bg-surface-muted"
              >
                Ver todo el periodo
              </button>
            </div>
          )}
        </div>
      )}
      <ChartLegend />
      <HistoryTable history={history} periodName={periodName} />
    </>
  );
}

/**
 * Evolución del valor de la cartera en Inicio (T2-18): selector de periodo, gráfica interactiva
 * (ratón y teclado), escala de tiempo para acercar, punto activo anunciado al lector de pantalla
 * y tabla alternativa. Cifras del backend con `calc_id` y una pista breve de dónde salen; la serie
 * usa precios de cierre, sin el impacto de eventos. Estilos en `chart.css`.
 */
export function PortfolioChart({ portfolioId }: { portfolioId: string }) {
  const [period, setPeriod] = useState<HistoryPeriod>(DEFAULT_PERIOD);
  const { data, isPending, isError, isPlaceholderData } = usePortfolioHistory(portfolioId, period);
  const periodName = PERIODS.find((p) => p.value === period)?.name ?? "";
  // Respuesta sin puntos (o inesperada): estado vacío, nunca una gráfica inventada.
  const hasPoints = Array.isArray(data?.points) && data.points.length > 0;

  return (
    <section aria-labelledby="chart-heading" className="kchart-card flex flex-col gap-4 rounded-card border border-line bg-surface pt-5 sm:pt-6">
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
          <ChartBody key={data.calc_id} history={data} period={period} periodName={periodName} />
        </div>
      )}
    </section>
  );
}
