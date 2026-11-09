import type { ExposureOut, PortfolioOut } from "../../api/generated/schema";
import { formatEur, formatPercent } from "../../lib/format";
import { Traced } from "../Traced";

interface TopCompaniesProps {
  exposure: ExposureOut;
  /** Para poner nombre a los activos en los que está cada empresa. */
  portfolio: PortfolioOut | undefined;
}

/**
 * Mayores empresas mirando dentro de los fondos y ETF, y en qué activos las tienes. Lo que
 * aparece en más de un activo se marca con texto ("En 3 activos"), no solo por posición.
 */
export function TopCompanies({ exposure, portfolio }: TopCompaniesProps) {
  const names = new Map((portfolio?.positions ?? []).map((p) => [p.asset_id, p.name]));
  const top = exposure.top_companies.slice(0, 10);
  return (
    <section
      aria-labelledby="top-empresas-title"
      className="rounded-card border border-line bg-surface"
    >
      <h3 id="top-empresas-title" className="m-0 px-6 pt-5 text-lg font-semibold text-ink">
        Mayores empresas, mirando dentro de tus fondos
      </h3>
      <div
        role="region"
        aria-label="Mayores empresas (desplázate para ver todas las columnas)"
        tabIndex={0}
        className="mt-2 overflow-x-auto"
      >
        <table className="w-full min-w-[40rem] border-collapse text-base">
          <caption className="sr-only">
            Diez mayores empresas de la cartera sumando lo que tienes directamente y lo que hay
            dentro de tus fondos y ETF
          </caption>
          <thead>
            <tr className="border-b border-line text-sm font-semibold text-ink-muted">
              <th scope="col" className="py-3 pl-6 pr-4 text-left">
                Empresa
              </th>
              <th scope="col" className="px-4 py-3 text-right">
                Peso
              </th>
              <th scope="col" className="px-4 py-3 text-right">
                Valor
              </th>
              <th scope="col" className="py-3 pl-4 pr-6 text-left">
                Dónde la tienes
              </th>
            </tr>
          </thead>
          <tbody>
            {top.map((c) => (
              <tr key={c.key} className="border-b border-line last:border-b-0">
                <th scope="row" className="py-3 pl-6 pr-4 text-left font-medium text-ink">
                  {c.name}
                </th>
                <td className="px-4 py-3 text-right tabular-nums">
                  <Traced calcId={exposure.calc_id}>{formatPercent(c.weight)}</Traced>
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  <Traced calcId={exposure.calc_id}>{formatEur(c.value_eur, 0)}</Traced>
                </td>
                <td className="py-3 pl-4 pr-6 text-ink-muted">
                  {c.held_in.length > 1 && (
                    <span className="mr-2 font-semibold text-ink">En {c.held_in.length} activos:</span>
                  )}
                  {c.held_in.map((h) => names.get(h.asset_id) ?? h.asset_id).join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
