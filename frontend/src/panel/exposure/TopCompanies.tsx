import type { CSSProperties } from "react";
import type { ExposureOut, PortfolioOut } from "../../api/generated/schema";
import { formatEur, formatPercent } from "../../lib/format";
import { Traced } from "../Traced";

interface TopCompaniesProps {
  exposure: ExposureOut;
  /** Para poner nombre a los activos en los que está cada empresa. */
  portfolio: PortfolioOut | undefined;
}

const BAR_COLORS = ["bg-chart-1", "bg-chart-2", "bg-chart-3", "bg-chart-4"] as const;

/**
 * Mayores empresas mirando dentro de los fondos y ETF, y en qué activos las tienes (T5-16: de
 * tabla a barras). Cada barra mide el peso frente al de la mayor, con la cifra exacta al lado;
 * el ancho es solo dibujo (`calc` con las fracciones tal cual llegan). Lo que aparece en más de un
 * activo se marca con texto ("En 3 activos"), no solo por posición.
 */
export function TopCompanies({ exposure, portfolio }: TopCompaniesProps) {
  const names = new Map((portfolio?.positions ?? []).map((p) => [p.asset_id, p.name]));
  const top = [...exposure.top_companies]
    .sort((a, b) => Number(b.weight) - Number(a.weight))
    .slice(0, 10);
  const max = top[0]?.weight;
  return (
    <section
      aria-labelledby="top-empresas-title"
      className="rounded-card border border-line bg-surface p-6"
    >
      <h3 id="top-empresas-title" className="m-0 text-lg font-semibold text-ink">
        Mayores empresas, mirando dentro de tus fondos
      </h3>
      <p className="m-0 mt-1 text-sm text-ink-muted">
        Peso en tu cartera y valor en euros, sumando lo que tienes directamente y lo que hay dentro
        de tus fondos y ETF. La barra compara cada una con la de más peso.
      </p>
      <ol
        aria-label="Diez mayores empresas de la cartera, de más a menos peso"
        className="m-0 mt-5 flex list-none flex-col gap-4 p-0"
      >
        {top.map((c, index) => (
          <li key={c.key} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1">
            <span className="text-base font-medium text-ink">{c.name}</span>
            <span className="text-right text-base tabular-nums text-ink">
              <Traced calcId={exposure.calc_id}>{formatPercent(c.weight)}</Traced>
              <span className="ml-2 text-sm text-ink-muted">
                <Traced calcId={exposure.calc_id}>{formatEur(c.value_eur, 0)}</Traced>
              </span>
            </span>
            <span aria-hidden="true" className="col-span-2 block h-2 rounded-full bg-surface-muted">
              <span
                className={`block h-full rounded-full ${BAR_COLORS[index % BAR_COLORS.length]!}`}
                style={
                  {
                    width: max ? `calc(${c.weight} / ${max} * 100%)` : "0",
                  } as CSSProperties
                }
              />
            </span>
            <span className="col-span-2 text-sm text-ink-muted">
              {c.held_in.length > 1 && (
                <span className="mr-1 font-semibold text-ink">En {c.held_in.length} activos:</span>
              )}
              {c.held_in.map((h) => names.get(h.asset_id) ?? h.asset_id).join(", ")}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
