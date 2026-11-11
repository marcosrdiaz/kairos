import { useCallback, useId, useMemo, useState, useSyncExternalStore } from "react";
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
import { MarkedChart } from "./markers/MarkedChart";
import { useEventMarkers } from "./markers/useEventMarkers";
import { useAlertNewsMarkers } from "./markers/useAlertNewsMarkers";
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
    <div className="flex flex-col gap-0.5 px-4 sm:px-5">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
        <p className="m-0 text-lg font-semibold tabular-nums text-ink">
          <TraceHint calcId={history.calc_id} text="Valor de tu cartera ese día: participaciones × precio de cierre." source={source}>
            {formatEur(row.raw)}
          </TraceHint>
        </p>
        <span className="text-base">
          <Change row={row} />
        </span>
      </div>
      <p className="m-0 text-sm text-ink-muted">
        Valor al cierre del {pointDate(row.date)}, sin el impacto estimado de los eventos.
      </p>
      <p className="m-0 text-sm text-ink-muted">
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
  portfolioId: string;
  history: PortfolioHistoryOut;
  period: HistoryPeriod;
  periodName: string;
  /** «Ajustar vista» abierto: escala de tiempo, leyenda y tabla. */
  adjustOpen: boolean;
  adjustId: string;
}

/** Gráfica y, plegado, «Ajustar vista». Se monta de nuevo al cambiar de serie (rango completo). */
function ChartBody({ portfolioId, history, period, periodName, adjustOpen, adjustId }: ChartBodyProps) {
  const compact = useCompact();
  const rows = useMemo(() => toRows(history), [history]);
  const markers = useEventMarkers(portfolioId, rows);
  const newsMarkers = useAlertNewsMarkers(portfolioId, rows);
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
      {/* En escritorio ancho la gráfica rellena el alto que le deja la fila (igual al de las tarjetas). */}
      <div className="pr-1 sm:pr-2 @min-[58rem]/app-content:min-h-[14.5rem] @min-[58rem]/app-content:flex-1">
        <MarkedChart
          className="h-[230px] sm:h-[300px] @min-[58rem]/app-content:h-full"
          fill
          rows={visible}
          markers={markers}
          newsMarkers={newsMarkers}
          period={period}
          startValue={startValue}
          label={`Valor de la cartera. ${periodName}. Usa las flechas para recorrer los días${
            markers.length + newsMarkers.length > 0 ? "; con Tab, las noticias marcadas" : ""
          }.`}
          store={store}
          reducedMotion={prefersReducedMotion()}
          compact={compact}
        />
      </div>
      {adjustOpen && (
        <div id={adjustId} className="flex flex-col gap-1 pb-3">
          <p className="m-0 px-4 text-sm text-ink-muted sm:px-5">
            Valor con precios de cierre. No incluye el impacto estimado de los eventos.
          </p>
          {rows.length >= RANGE_MIN_POINTS && (
            <div className="flex flex-col gap-1">
              <RangeSelector rows={rows} start={range.start} end={range.end} onChange={onRange} />
              {zoomed && (
                <div className="flex justify-end px-4 sm:px-5">
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
          <HistoryTable history={history} periodName={periodName} markers={markers} newsMarkers={newsMarkers} />
        </div>
      )}
    </>
  );
}

/**
 * Evolución del valor de la cartera en Inicio (T2-18): selector de periodo, gráfica interactiva
 * (ratón y teclado) y punto activo anunciado al lector de pantalla. La escala de tiempo, la
 * leyenda y la tabla alternativa van plegadas en «Ajustar vista» (TX-01), para que la tarjeta quepa
 * junto a las de estado. Cifras del backend con `calc_id` y una pista breve de dónde salen; la
 * serie usa precios de cierre, sin el impacto de eventos. Estilos en `chart.css`.
 */
export function PortfolioChart({ portfolioId }: { portfolioId: string }) {
  const [period, setPeriod] = useState<HistoryPeriod>(DEFAULT_PERIOD);
  const { data, isPending, isError, isPlaceholderData } = usePortfolioHistory(portfolioId, period);
  const periodName = PERIODS.find((p) => p.value === period)?.name ?? "";
  // Respuesta sin puntos (o inesperada): estado vacío, nunca una gráfica inventada.
  const hasPoints = Array.isArray(data?.points) && data.points.length > 0;

  const [adjustOpen, setAdjustOpen] = useState(false);
  const adjustId = useId();

  return (
    <section aria-labelledby="chart-heading" className="kchart-card flex flex-col gap-3 rounded-card border border-line bg-surface pt-4 @min-[58rem]/app-content:h-full">
      <ChartBackdrop />
      <div className="kchart-header flex flex-col gap-2 px-4 sm:px-5">
        <h2 id="chart-heading" className="m-0 whitespace-nowrap text-base font-semibold text-ink sm:text-lg">
          Evolución de tu cartera
        </h2>
        <div className="flex flex-wrap items-center gap-2 @min-[58rem]/app-content:flex-nowrap">
          <PeriodPicker value={period} onChange={setPeriod} />
          {hasPoints && (
            <button
              type="button"
              aria-expanded={adjustOpen}
              aria-controls={adjustOpen ? adjustId : undefined}
              onClick={() => setAdjustOpen((open) => !open)}
              className="inline-flex min-h-touch shrink-0 items-center gap-2 rounded-full border border-line-strong bg-surface px-4 text-sm font-semibold text-accent hover:bg-surface-muted"
            >
              Ajustar vista
              <svg viewBox="0 0 24 24" className={`size-4 transition-transform duration-200 ${adjustOpen ? "rotate-180" : ""}`} fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path d="m6 9 6 6 6-6" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {isPending && (
        <div role="status" aria-label="Cargando la evolución de tu cartera" className="mx-4 mb-4 h-60 rounded-control bg-surface-muted motion-safe:animate-pulse sm:mx-5 @min-[58rem]/app-content:flex-1" />
      )}
      {isError && !data && (
        <div className="mx-4 mb-4 sm:mx-5">
          <EmptyNote>Ahora mismo no podemos mostrar la evolución de tu cartera. Vuelve a intentarlo en un rato.</EmptyNote>
        </div>
      )}
      {data && !hasPoints && (
        <div className="mx-4 mb-4 sm:mx-5">
          <EmptyNote>Todavía no hay cierres para este periodo.</EmptyNote>
        </div>
      )}
      {data && hasPoints && (
        <div
          aria-busy={isPlaceholderData}
          className={`flex flex-col gap-2 transition-opacity duration-200 @min-[58rem]/app-content:min-h-0 @min-[58rem]/app-content:flex-1 ${isPlaceholderData ? "opacity-60" : ""}`}
        >
          <ChartBody key={data.calc_id} portfolioId={portfolioId} history={data} period={period} periodName={periodName} adjustOpen={adjustOpen} adjustId={adjustId} />
        </div>
      )}
    </section>
  );
}
