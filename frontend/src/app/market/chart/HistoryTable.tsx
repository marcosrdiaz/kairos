import { Fragment, memo, useMemo, useRef, useState } from "react";
import type { PortfolioHistoryOut } from "../../../api/generated/schema";
import { Scrollbar } from "../../../components/Scrollbar";
import { formatEur } from "../../../lib/format";
import { Change, FlowTag } from "./Change";
import { monthOf, pointDate, toRows, trendOf, weekdayOf, type ChartRow } from "./chartFormat";

interface HistoryTableProps {
  history: PortfolioHistoryOut;
  periodName: string;
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

function Rows({ history, periodName }: HistoryTableProps) {
  const groups = useMemo(() => byMonth(toRows(history)), [history]);
  const scroller = useRef<HTMLDivElement>(null);
  return (
    <div className="relative border-t border-line">
      <div ref={scroller} className="kairos-scroll max-h-96 overflow-y-auto">
        <table className="w-full border-collapse text-base">
          <caption className="sr-only">
            Valor de la cartera por día y variación respecto al cierre anterior. {periodName}.
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
 * las aportaciones en azul. Plegada por defecto; las
 * filas solo se pintan al abrirla. Barra de scroll propia (`components/Scrollbar`).
 */
export const HistoryTable = memo(function HistoryTable({ history, periodName }: HistoryTableProps) {
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
      {open && <Rows history={history} periodName={periodName} />}
    </details>
  );
});
