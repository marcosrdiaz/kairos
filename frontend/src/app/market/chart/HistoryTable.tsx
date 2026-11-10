import type { PortfolioHistoryOut } from "../../../api/generated/schema";
import { formatEur } from "../../../lib/format";
import { pointDate } from "./chartFormat";

/**
 * Tabla alternativa a la gráfica: los mismos puntos, del más reciente al más antiguo.
 * Plegada por defecto para no alargar Inicio; el lector de pantalla la encuentra por su título.
 */
export function HistoryTable({ history, periodName }: { history: PortfolioHistoryOut; periodName: string }) {
  const rows = [...history.points].reverse();
  return (
    <details className="group rounded-control border border-line">
      <summary className="flex min-h-touch cursor-pointer items-center px-4 text-base font-medium text-accent">
        Ver los datos en una tabla
      </summary>
      <div className="max-h-80 overflow-y-auto border-t border-line">
        <table className="w-full border-collapse text-base">
          <caption className="sr-only">Valor de la cartera por día. {periodName}.</caption>
          <thead className="sticky top-0 bg-surface">
            <tr>
              <th scope="col" className="px-4 py-2 text-left text-sm font-medium text-ink-muted">
                Fecha
              </th>
              <th scope="col" className="px-4 py-2 text-right text-sm font-medium text-ink-muted">
                Valor
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.date} className="border-t border-line">
                <th scope="row" className="px-4 py-2 text-left font-normal text-ink">
                  {pointDate(p.date)}
                </th>
                <td className="px-4 py-2 text-right tabular-nums text-ink" data-calc-id={history.calc_id}>
                  {formatEur(p.value_eur)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
