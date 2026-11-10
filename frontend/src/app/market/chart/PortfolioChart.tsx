import { useCallback, useMemo, useState } from "react";
import type { HistoryPeriod, PortfolioHistoryOut } from "../../../api/generated/schema";
import { usePortfolioHistory } from "../../../api/hooks/usePortfolioHistory";
import { EmptyNote } from "../../../components/PageTitle";
import { TraceFigure } from "../../../components/trace/TraceFigure";
import { formatEur } from "../../../lib/format";
import { DEFAULT_PERIOD, PERIODS, pointDate, toRows, type ChartRow } from "./chartFormat";
import { HistoryChart } from "./HistoryChart";
import { HistoryTable } from "./HistoryTable";
import { PeriodPicker } from "./PeriodPicker";

function prefersReducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Aportaciones o retiradas del periodo, para no confundirlas con rentabilidad. */
function FlowsNote({ history }: { history: PortfolioHistoryOut }) {
  const flows = history.net_flows_eur;
  if (Number(flows) === 0) {
    return <>Sin aportaciones ni retiradas en el periodo.</>;
  }
  const amount = flows.startsWith("-") ? flows.slice(1) : flows;
  return (
    <>
      {flows.startsWith("-") ? "Incluye retiradas por " : "Incluye aportaciones por "}
      <TraceFigure calcId={history.calc_id}>{formatEur(amount)}</TraceFigure>.
    </>
  );
}

/** Valor del punto activo (o del último) en grande, con su fecha y el valor al empezar. */
function Readout({ history, active }: { history: PortfolioHistoryOut; active: ChartRow | null }) {
  const last = history.points[history.points.length - 1];
  const raw = active?.raw ?? last?.value_eur;
  const date = active?.date ?? last?.date;
  if (!raw || !date) return null;
  return (
    <div className="flex flex-wrap items-end gap-x-8 gap-y-2">
      {/* Ancho fijo: al recorrer la serie, el bloque de al lado no baila. */}
      <div className="min-w-64">
        <p className="m-0 text-2xl font-semibold tabular-nums text-ink">
          <TraceFigure calcId={history.calc_id}>{formatEur(raw)}</TraceFigure>
        </p>
        <p className="m-0 text-sm text-ink-muted">{active ? pointDate(date) : `Último cierre: ${pointDate(date)}`}</p>
      </div>
      <p className="m-0 text-sm text-ink-muted">
        Al empezar el periodo:{" "}
        <span className="font-semibold tabular-nums text-ink">
          <TraceFigure calcId={history.calc_id}>{formatEur(history.start_value_eur)}</TraceFigure>
        </span>
        <br />
        <FlowsNote history={history} />
      </p>
    </div>
  );
}

/**
 * Evolución del valor de la cartera en Inicio (T2-18): selector de periodo, gráfica interactiva
 * (ratón y teclado), punto activo anunciado al lector de pantalla y tabla alternativa.
 * Cifras del backend con `calc_id`; la serie usa precios de cierre, sin el impacto de eventos.
 */
export function PortfolioChart({ portfolioId }: { portfolioId: string }) {
  const [period, setPeriod] = useState<HistoryPeriod>(DEFAULT_PERIOD);
  const [active, setActive] = useState<ChartRow | null>(null);
  const onActiveChange = useCallback((row: ChartRow | null) => setActive(row), []);
  const { data, isPending, isError, isPlaceholderData } = usePortfolioHistory(portfolioId, period);
  const periodName = PERIODS.find((p) => p.value === period)?.name ?? "";
  // Respuesta sin puntos (o inesperada): estado vacío, nunca una gráfica inventada.
  const hasPoints = Array.isArray(data?.points) && data.points.length > 0;
  // Filas estables entre renders: la gráfica y su efecto de punto activo dependen de ellas.
  const rows = useMemo(() => (data && hasPoints ? toRows(data) : []), [data, hasPoints]);

  return (
    <section aria-labelledby="chart-heading" className="flex flex-col gap-4 rounded-card border border-line bg-surface p-5 lg:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 id="chart-heading" className="m-0 mb-1 text-lg font-semibold text-ink">
            Evolución de tu cartera
          </h2>
          <p className="m-0 text-sm text-ink-muted">
            Valor con precios de cierre. No incluye el impacto estimado de los eventos.
          </p>
        </div>
        <PeriodPicker value={period} onChange={(p) => { setActive(null); setPeriod(p); }} />
      </div>

      {isPending && (
        <div role="status" aria-label="Cargando la evolución de tu cartera" className="h-80 rounded-control bg-surface-muted motion-safe:animate-pulse" />
      )}
      {isError && !data && (
        <EmptyNote>Ahora mismo no podemos mostrar la evolución de tu cartera. Vuelve a intentarlo en un rato.</EmptyNote>
      )}
      {data && !hasPoints && <EmptyNote>Todavía no hay cierres para este periodo.</EmptyNote>}
      {data && hasPoints && (
        <div
          aria-busy={isPlaceholderData}
          className={`flex flex-col gap-4 transition-opacity duration-200 ${isPlaceholderData ? "opacity-60" : ""}`}
        >
          <Readout history={data} active={active} />
          <p className="sr-only" aria-live="polite">
            {active ? `${pointDate(active.date)}: ${formatEur(active.raw)}` : ""}
          </p>
          <HistoryChart
            key={`${period}-${rows.length}`}
            rows={rows}
            period={period}
            label={`Valor de la cartera. ${periodName}. Usa las flechas para recorrer los días.`}
            onActiveChange={onActiveChange}
            reducedMotion={prefersReducedMotion()}
          />
          <HistoryTable history={data} periodName={periodName} />
        </div>
      )}
    </section>
  );
}
