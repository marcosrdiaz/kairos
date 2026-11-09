import type { PortfolioOut } from "../../api/generated/schema";
import { formatPrice } from "../../app/operations/usePortfolio";
import { formatDate, formatEur, formatPercent, formatUnits } from "../../lib/format";
import { signedEur } from "../figures";
import { Traced } from "../Traced";

const th = "px-4 py-3 text-left text-sm font-semibold text-ink-muted";
const num = "px-4 py-3 text-right tabular-nums";

/**
 * Posiciones con cifra exacta y la fecha del precio de cada una. Los fondos cotizan una vez al
 * día (valor liquidativo) y los ETF y acciones durante la sesión; la fecha lo deja claro.
 */
export function PositionsTable({ portfolio }: { portfolio: PortfolioOut }) {
  return (
    <div className="mt-4 rounded-card border border-line bg-surface">
      <h3 className="m-0 px-6 pt-5 text-lg font-semibold text-ink">Posiciones</h3>
      <div
        role="region"
        aria-label="Posiciones (desplázate para ver todas las columnas)"
        tabIndex={0}
        className="mt-2 overflow-x-auto"
      >
        <table className="w-full min-w-[44rem] border-collapse text-base">
          <caption className="sr-only">
            Posiciones de la cartera de {portfolio.name}, con su valor en euros y la fecha del precio
          </caption>
          <thead>
            <tr className="border-b border-line">
              <th scope="col" className={`${th} pl-6`}>
                Activo
              </th>
              <th scope="col" className={`${th} text-right`}>
                Participaciones
              </th>
              <th scope="col" className={`${th} text-right`}>
                Precio
              </th>
              <th scope="col" className={`${th} text-right`}>
                Valor
              </th>
              <th scope="col" className={`${th} text-right`}>
                Peso
              </th>
              <th scope="col" className={`${th} pr-6 text-right`}>
                Plusvalía latente
              </th>
            </tr>
          </thead>
          <tbody>
            {portfolio.positions.map((pos) => (
              <tr key={pos.asset_id} className="border-b border-line last:border-b-0">
                <th scope="row" className="py-3 pl-6 pr-4 text-left font-medium text-ink">
                  {pos.name}
                  <span className="block text-sm font-normal text-ink-muted">
                    {pos.ticker ?? pos.isin}
                  </span>
                </th>
                <td className={num}>{formatUnits(pos.units)}</td>
                <td className={num}>
                  {formatPrice(pos.price, pos.price_currency)}
                  <span className="block text-sm text-ink-muted">
                    <time dateTime={pos.price_at}>{formatDate(pos.price_at)}</time>
                  </span>
                </td>
                <td className={`${num} font-semibold text-ink`}>
                  <Traced calcId={portfolio.calc_id}>{formatEur(pos.value_eur)}</Traced>
                </td>
                <td className={num}>{formatPercent(pos.weight)}</td>
                <td className={`${num} pr-6`}>{signedEur(pos.unrealized_pnl_eur)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
