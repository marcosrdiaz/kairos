import { Fragment, memo, useMemo, useRef, useState } from "react";
import type { PortfolioHistoryOut } from "../../../api/generated/schema";
import { Scrollbar } from "../../../components/Scrollbar";
import { formatEur, formatEurRange } from "../../../lib/format";
import { Change, FlowTag } from "./Change";
import { monthOf, pointDate, toRows, trendOf, weekdayOf, type ChartRow } from "./chartFormat";
import { EVENT_TYPE_LABEL } from "../../news/labels";
import { sessionsText } from "../../news-feed/labels";
import { markerImpact } from "./markers/markerText";
import { markersByDate, type EventMarker } from "./markers/placeMarkers";
import type { AlertNewsMarker } from "./markers/useAlertNewsMarkers";

interface HistoryTableProps {
  history: PortfolioHistoryOut;
  periodName: string;
  /** Noticias colocadas en la serie (T2-22): salen en la fila de su cierre. */
  markers?: EventMarker[];
  newsMarkers?: AlertNewsMarker[];
  /** De qué es la serie, para el lector de pantalla: «la cartera» o el nombre de una posición. */
  subject?: string;
}

/** Noticia en la tabla: tipo, título e impacto como rango (cifras del backend). */
function EventTag({ marker }: { marker: EventMarker }) {
  const e = marker.event;
  const { range } = markerImpact(marker);
  return (
    <span className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 rounded-control border border-line bg-surface px-2 py-1 text-sm text-ink" data-calc-id={e.calc_id}>
      <span className="font-semibold text-accent">{EVENT_TYPE_LABEL[e.event_type]}</span>
      <span>{e.title}</span>
      <span className="text-ink-muted">
        · impacto {range} ({pointDate(marker.marketDate)})
      </span>
    </span>
  );
}

function NewsTag({ marker }: { marker: AlertNewsMarker }) {
  const estimate = marker.news.estimate;
  const range =
    estimate &&
    (estimate.status === "estimated" || estimate.status === "measured") &&
    estimate.low_eur != null &&
    estimate.high_eur != null
      ? {
          low: estimate.low_eur,
          high: estimate.high_eur,
          status: estimate.status,
          horizon: estimate.horizon_sessions,
        }
      : null;
  return (
    <span className="mt-1 flex flex-wrap gap-x-2 rounded-control border border-line bg-surface px-2 py-1 text-sm text-ink" data-calc-id={estimate?.calc_id ?? undefined}>
      <span className="font-semibold text-brand-red">Noticia con aviso</span>
      <span>{marker.news.title}</span>
      <span className="text-ink-muted">{pointDate(marker.marketDate)}
        {range
          ? ` · impacto ${range.status === "measured" ? "medido" : "estimado"} ${formatEurRange(range.low, range.high)}${range.horizon ? ` a ${sessionsText(range.horizon)}` : ""}`
          : ""}
      </span>
    </span>
  );
}

/** Puntos agrupados por mes, del más reciente al más antiguo. */
function byMonth(rows: ChartRow[]) {
  const groups: { month: string; rows: ChartRow[] }[] = [];
  for (const r of [...rows].reverse()) {
    const month = monthOf(r.date);
    const current = groups[groups.length - 1];
    if (current?.month === month) current.rows.push(r);
    else groups.push({ month, rows: [r] });
  }
  return groups;
}

function Rows({ history, periodName, markers = [], newsMarkers = [], subject = "la cartera" }: HistoryTableProps) {
  const groups = useMemo(() => byMonth(toRows(history)), [history]);
  const byDate = useMemo(() => markersByDate(markers), [markers]);
  const newsByDate = useMemo(() => {
    const map = new Map<string, AlertNewsMarker[]>();
    for (const marker of newsMarkers) map.set(marker.date, [...(map.get(marker.date) ?? []), marker]);
    return map;
  }, [newsMarkers]);
  const scroller = useRef<HTMLDivElement>(null);
  return (
    <div className="relative border-t border-line">
      <div ref={scroller} className="kairos-scroll max-h-96 overflow-y-auto">
        <table className="w-full border-collapse text-base">
          <caption className="sr-only">
            Valor de {subject} por día y variación respecto al cierre anterior. {periodName}.
          </caption>
          <thead className="sticky top-0 z-10">
            <tr>
              <th scope="col" className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Fecha
              </th>
              <th scope="col" className="px-4 py-2.5 pr-6 text-right text-xs font-semibold uppercase tracking-wider text-ink-muted sm:pr-4">
                Valor<span className="sm:hidden"> y variación</span>
              </th>
              <th scope="col" className="hidden px-4 py-2.5 pr-6 text-right text-xs font-semibold uppercase tracking-wider text-ink-muted sm:table-cell">
                Variación
              </th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <Fragment key={g.month}>
                <tr className="kchart-month">
                  <th scope="colgroup" colSpan={3} className="px-4 pb-1 pt-3 text-left text-sm font-semibold text-ink">
                    {g.month}
                  </th>
                </tr>
                {g.rows.map((r) => (
                  <tr key={r.date} className="kchart-row border-t border-line" data-trend={trendOf(r.change)}>
                    <th scope="row" className="px-4 py-2 text-left font-normal text-ink">
                      <span className="mr-2 hidden min-w-14 justify-center rounded-full bg-surface-muted px-2 py-0.5 text-sm text-ink-muted sm:inline-flex" aria-hidden="true">
                        {weekdayOf(r.date)}
                      </span>
                      <span className="hidden sm:inline">{pointDate(r.date)}</span>
                      {/* En móvil, fecha corta para que quepan el valor y la variación. */}
                      <span className="sm:hidden">{weekdayOf(r.date)}</span>
                      {byDate.get(r.date)?.map((m) => <EventTag key={m.event.event_id} marker={m} />)}
                      {newsByDate.get(r.date)?.map((m) => <NewsTag key={m.news.id} marker={m} />)}
                    </th>
                    <td className="px-4 py-2 pr-6 text-right font-medium tabular-nums text-ink sm:pr-4" data-calc-id={history.calc_id}>
                      {formatEur(r.raw)}
                      {/* En móvil, la variación va debajo del valor (sin tercera columna). */}
                      <span className="mt-1 flex flex-col items-end gap-1 text-sm font-normal sm:hidden">
                        <Change row={r} compact />
                        <FlowTag row={r} />
                      </span>
                    </td>
                    <td className="hidden px-4 py-2 pr-6 text-right text-sm sm:table-cell" data-calc-id={history.calc_id}>
                      <span className="flex flex-col items-end gap-1">
                        <Change row={r} />
                        <FlowTag row={r} />
                      </span>
                    </td>
                  </tr>
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
      <Scrollbar target={scroller} />
    </div>
  );
}

/**
 * Tabla alternativa a la gráfica: los mismos puntos, agrupados por mes, con la variación respecto
 * al cierre anterior (flecha, signo y color; la fila, con un fondo muy suave verde o granate) y
 * las aportaciones en azul; las noticias de la gráfica (T2-22) salen en la fila de su cierre.
 * Plegada por defecto; las filas solo se pintan al abrirla. Barra de scroll propia.
 */
export const HistoryTable = memo(function HistoryTable({ history, periodName, markers, newsMarkers, subject }: HistoryTableProps) {
  const [open, setOpen] = useState(false);
  return (
    <details
      className="kchart-table mx-5 mb-5 overflow-hidden rounded-2xl border border-line bg-surface sm:mx-6 sm:mb-6"
      onToggle={(e) => setOpen(e.currentTarget.open)}
    >
      <summary className="flex min-h-touch cursor-pointer list-none items-center justify-between gap-3 px-4 py-2 text-base font-semibold text-accent hover:bg-surface-muted">
        <span>
          Ver tabla{" "}
          <span className="font-normal text-ink-muted">({history.points.length} cierres)</span>
        </span>
        <svg viewBox="0 0 24 24" className="kchart-chevron size-5 shrink-0 transition-transform duration-200" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </summary>
      {open && <Rows history={history} periodName={periodName} markers={markers} newsMarkers={newsMarkers} subject={subject} />}
    </details>
  );
});
