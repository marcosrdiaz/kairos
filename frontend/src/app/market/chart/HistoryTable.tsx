import { Fragment, useMemo } from "react";
import type { PortfolioHistoryOut } from "../../../api/generated/schema";
import { formatEur } from "../../../lib/format";
import { monthOf, pointDate, weekdayOf } from "./chartFormat";

interface HistoryTableProps {
  history: PortfolioHistoryOut;
  periodName: string;
  /** Fecha del punto activo de la gráfica: su fila se resalta. */
  activeDate: string | null;
}

/** Puntos agrupados por mes, del más reciente al más antiguo. */
function byMonth(points: PortfolioHistoryOut["points"]) {
  const groups: { month: string; points: PortfolioHistoryOut["points"] }[] = [];
  for (const p of [...points].reverse()) {
    const month = monthOf(p.date);
    const current = groups[groups.length - 1];
    if (current?.month === month) current.points.push(p);
    else groups.push({ month, points: [p] });
  }
  return groups;
}

/**
 * Tabla alternativa a la gráfica: los mismos puntos, agrupados por mes con una cabecera de mes
 * fija al desplazarse. Plegada por defecto; el lector de pantalla la encuentra por su título.
 */
export function HistoryTable({ history, periodName, activeDate }: HistoryTableProps) {
  const groups = useMemo(() => byMonth(history.points), [history.points]);
  return (
    <details className="kchart-table group mx-5 mb-5 overflow-hidden rounded-2xl border border-line bg-surface sm:mx-6 sm:mb-6">
      <summary className="flex min-h-touch cursor-pointer list-none items-center justify-between gap-3 px-4 py-2 text-base font-semibold text-accent hover:bg-accent-tint">
        <span>
          Ver los datos en una tabla{" "}
          <span className="font-normal text-ink-muted">({history.points.length} cierres)</span>
        </span>
        <svg viewBox="0 0 24 24" className="kchart-chevron size-5 shrink-0 transition-transform duration-200" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </summary>
      <div className="max-h-96 overflow-y-auto border-t border-line">
        <table className="w-full border-collapse text-base">
          <caption className="sr-only">Valor de la cartera por día. {periodName}.</caption>
          <thead className="sticky top-0 z-10">
            <tr>
              <th scope="col" className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Fecha
              </th>
              <th scope="col" className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Valor
              </th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <Fragment key={g.month}>
                <tr className="kchart-month">
                  <th scope="colgroup" colSpan={2} className="px-4 py-1.5 text-left text-sm font-semibold capitalize text-ink">
                    {g.month}
                  </th>
                </tr>
                {g.points.map((p) => (
                  <tr key={p.date} className="kchart-row border-t border-line" data-active={p.date === activeDate ? "" : undefined}>
                    <th scope="row" className="px-4 py-2 text-left font-normal text-ink">
                      <span className="mr-2 inline-flex min-w-14 justify-center rounded-full bg-surface-muted px-2 py-0.5 text-sm text-ink-muted" aria-hidden="true">
                        {weekdayOf(p.date)}
                      </span>
                      {pointDate(p.date)}
                    </th>
                    <td className="px-4 py-2 text-right font-medium tabular-nums text-ink" data-calc-id={history.calc_id}>
                      {formatEur(p.value_eur)}
                    </td>
                  </tr>
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
