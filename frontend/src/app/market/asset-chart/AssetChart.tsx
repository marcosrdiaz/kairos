import { useCallback, useMemo, useState, useSyncExternalStore } from "react";
import type { AssetHistoryOut, HistoryPeriod } from "../../../api/generated/schema";
import { ApiError } from "../../../api/client";
import { useAssetHistory } from "../../../api/hooks/useAssetHistory";
import { useEvents } from "../../../api/hooks/useEvents";
import { EmptyNote } from "../../../components/PageTitle";
import { formatEur, formatUnits } from "../../../lib/format";
import { formatPrice } from "../../operations/usePortfolio";
import { createActivePointStore, useActivePoint, type ActivePointStore } from "../chart/activePoint";
import "../chart/chart.css";
import { ChartBackdrop } from "../chart/ChartBackdrop";
import { ChartLegend } from "../chart/ChartLegend";
import { Change } from "../chart/Change";
import { DEFAULT_PERIOD, PERIODS, chipDate, pointDate, signedEur, toRows } from "../chart/chartFormat";
import { HistoryTable } from "../chart/HistoryTable";
import { MarkedChart } from "../chart/markers/MarkedChart";
import { PeriodPicker } from "../chart/PeriodPicker";
import { RangeSelector } from "../chart/RangeSelector";
import { TraceHint } from "../chart/TraceHint";
import { placeAssetMarkers } from "./assetMarkers";

/** Desde cuántos puntos se ofrece la escala de tiempo para acotar el rango. */
const RANGE_MIN_POINTS = 10;
const COMPACT = "(max-width: 39.999rem)";

function prefersReducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

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

function sourceLine(history: AssetHistoryOut): string {
  const fx = history.sources.some((s) => s.kind === "fx") ? " y tipo de cambio" : "";
  const last = history.points.at(-1);
  return `Precios de cierre de ${history.name}${fx}. Datos a ${last ? chipDate(last.date) : "—"}.`;
}

const DOT = <span className="mx-2 text-ink-muted" aria-hidden="true">·</span>;

/** Valor de la posición en el punto activo (o el último), con su precio y participaciones. */
function Readout({ history, store }: { history: AssetHistoryOut; store: ActivePointStore }) {
  const active = useActivePoint(store);
  const byDate = useMemo(() => new Map(history.points.map((p) => [p.date, p])), [history]);
  const lastRow = useMemo(() => toRows(history).at(-1) ?? null, [history]);
  const row = active ?? lastRow;
  const point = row ? byDate.get(row.date) : undefined;
  if (!row || !point) return null;
  const source = sourceLine(history);
  const flows = history.net_flows_eur;
  const noFlows = Number(flows) === 0;
  return (
    <div className="flex flex-col gap-1 px-5 sm:px-6">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <p className="m-0 text-3xl font-semibold tabular-nums text-ink sm:text-4xl">
          <TraceHint calcId={history.calc_id} text="Valor de la posición ese día: participaciones × precio de cierre × tipo de cambio." source={source}>
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
          Precio:{" "}
          <span className="font-semibold tabular-nums text-ink">{formatPrice(point.price, history.currency)}</span>
        </span>
        {DOT}
        <span className="tabular-nums">{formatUnits(point.units)} participaciones</span>
      </p>
      <p className="m-0 text-sm text-ink-muted">
        <span>
          Al empezar el periodo:{" "}
          <span className="font-semibold tabular-nums text-ink">{formatEur(history.start_value_eur)}</span>
        </span>
        {DOT}
        {noFlows ? (
          <span>Sin compras ni ventas en el periodo.</span>
        ) : (
          <span>
            {flows.startsWith("-") ? "Ventas: " : "Compras: "}
            <span className="font-semibold tabular-nums text-info">
              <TraceHint calcId={history.calc_id} text="Dinero que entró o salió de esta posición en el periodo. No es rentabilidad." source={source}>
                {signedEur(flows)}
              </TraceHint>
            </span>
          </span>
        )}
      </p>
    </div>
  );
}

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
  history: AssetHistoryOut;
  period: HistoryPeriod;
  periodName: string;
}

function ChartBody({ portfolioId, history, period, periodName }: ChartBodyProps) {
  const compact = useCompact();
  const rows = useMemo(() => toRows(history), [history]);
  const { data: events } = useEvents(portfolioId);
  const markers = useMemo(
    () => placeAssetMarkers(rows, events ?? [], history.asset_id),
    [rows, events, history.asset_id],
  );
  const [store] = useState(createActivePointStore);
  const [range, setRange] = useState({ start: 0, end: rows.length - 1 });
  const visible = useMemo(() => rows.slice(range.start, range.end + 1), [rows, range]);
  const onRange = useCallback((start: number, end: number) => setRange({ start, end }), []);
  const zoomed = range.start > 0 || range.end < rows.length - 1;
  return (
    <>
      <Readout history={history} store={store} />
      <LiveActive store={store} />
      <div className="pr-1 sm:pr-2">
        <MarkedChart
          rows={visible}
          markers={markers}
          period={period}
          startValue={Number(history.start_value_eur)}
          label={`Valor de ${history.name}. ${periodName}. Usa las flechas para recorrer los días${
            markers.length > 0 ? "; con Tab, las noticias marcadas" : ""
          }.`}
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
      <ChartLegend subject="position" />
      <HistoryTable history={history} periodName={periodName} markers={markers} subject={history.name} />
    </>
  );
}

/**
 * Evolución de una posición (T2-23): la gráfica de Inicio con la serie de un solo activo (precio de
 * cierre o VL en su divisa, participaciones y valor en euros) y solo las noticias que le afectan,
 * con su impacto en esta posición como rango. Cifras del backend con `calc_id`.
 */
export function AssetChart({ portfolioId, assetId }: { portfolioId: string; assetId: string }) {
  const [period, setPeriod] = useState<HistoryPeriod>(DEFAULT_PERIOD);
  const { data, isPending, isError, error, isPlaceholderData } = useAssetHistory(portfolioId, assetId, period);
  const periodName = PERIODS.find((p) => p.value === period)?.name ?? "";
  const hasPoints = Array.isArray(data?.points) && data.points.length > 0;
  const notHeld = error instanceof ApiError && error.status === 404;

  return (
    <section aria-labelledby="asset-chart-heading" className="kchart-card flex flex-col gap-4 rounded-card border border-line bg-surface pt-5 sm:pt-6">
      <ChartBackdrop />
      <div className="flex flex-col gap-4 px-5 sm:flex-row sm:items-start sm:justify-between sm:px-6">
        <div>
          <h2 id="asset-chart-heading" className="m-0 mb-1 text-lg font-semibold text-ink">
            {data ? `Evolución de ${data.name}` : "Evolución de la posición"}
          </h2>
          <p className="m-0 text-sm text-ink-muted">
            Valor con precios de cierre. No incluye el impacto estimado de los eventos.
          </p>
        </div>
        <PeriodPicker value={period} onChange={setPeriod} />
      </div>

      {isPending && (
        <div role="status" aria-label="Cargando la evolución de la posición" className="mx-5 mb-5 h-80 rounded-control bg-surface-muted motion-safe:animate-pulse sm:mx-6" />
      )}
      {isError && !data && (
        <div className="mx-5 mb-5 sm:mx-6">
          <EmptyNote>
            {notHeld
              ? "Esta cartera no ha tenido nunca ese activo."
              : "Ahora mismo no podemos mostrar la evolución de esta posición. Vuelve a intentarlo en un rato."}
          </EmptyNote>
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
          <ChartBody key={data.calc_id} portfolioId={portfolioId} history={data} period={period} periodName={periodName} />
        </div>
      )}
    </section>
  );
}
