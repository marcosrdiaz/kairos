import type { Ref } from "react";
import type { PortfolioOut } from "../../api/generated/schema";
import { formatDate, formatEur, formatPercent } from "../../lib/format";
import { ASSET_CLASS_LABEL, ASSET_CLASS_ORDER } from "./labels";

const isZero = (fraction: string) => /^0*(?:\.0*)?$/.test(fraction);

interface OnboardingResultProps {
  portfolio: PortfolioOut;
  ref?: Ref<HTMLElement>;
}

/**
 * Lo que devuelve el alta (`PortfolioOut`): valor y asignación ya recalculados por el gestor
 * de cartera (RF-01). Ninguna cifra se calcula aquí; `data-calc-id` apunta a su traza.
 * Recibe el foco al aparecer para que el lector lo lea.
 */
export function OnboardingResult({ portfolio, ref }: OnboardingResultProps) {
  const classes = ASSET_CLASS_ORDER.filter((c) => !isZero(portfolio.allocation[c]));
  return (
    <section
      ref={ref}
      tabIndex={-1}
      aria-labelledby="onboarding-result-title"
      data-calc-id={portfolio.calc_id}
      className="flex flex-col gap-4 rounded-card border border-line bg-surface-muted p-5"
    >
      <h3 id="onboarding-result-title" className="m-0 text-lg font-semibold text-success">
        Posiciones guardadas en la cartera de {portfolio.name}
      </h3>
      <dl className="m-0 grid gap-x-6 gap-y-3 sm:grid-cols-[auto_1fr]">
        <dt className="text-ink-muted">Valor total</dt>
        <dd className="m-0 font-semibold text-ink tabular-nums">{formatEur(portfolio.total_eur)}</dd>
        <dt className="text-ink-muted">Posiciones</dt>
        <dd className="m-0 text-ink tabular-nums">{portfolio.positions.length}</dd>
        <dt className="text-ink-muted">Valorada a</dt>
        <dd className="m-0 text-ink">{formatDate(portfolio.valued_at)}</dd>
      </dl>
      <div>
        <h4 className="m-0 mb-2 text-base font-semibold text-ink">Asignación</h4>
        <ul className="m-0 flex list-none flex-wrap gap-2 p-0">
          {classes.map((c) => (
            <li key={c} className="rounded-full bg-surface px-3 py-1 text-base text-ink tabular-nums">
              {ASSET_CLASS_LABEL[c]}: {formatPercent(portfolio.allocation[c])}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
