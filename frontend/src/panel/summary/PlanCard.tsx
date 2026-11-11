import type { ReactNode } from "react";
import type { PlanOut } from "../../api/generated/schema";
import { isPlanMissing, usePlan } from "../../api/hooks/usePlan";
import { formatEur, formatPercent, formatWeight } from "../../lib/format";
import { ProgressBar } from "../../ui/ProgressBar";
import { trendOf } from "../../widget/states";
import { Traced } from "../Traced";

/** "0.0234" -> "2,3 puntos"; el signo lo dice la frase, no la cifra. */
function points(fraction: string): string {
  return formatPercent(fraction.trim().replace(/^[+-]/, "")).replace(/\s?%$/, " puntos");
}

function driftSentence(plan: PlanOut): string {
  const trend = trendOf(plan.drift_equity);
  if (trend === "flat") return "La renta variable está justo en el objetivo de tu plan.";
  const side = trend === "up" ? "por encima" : "por debajo";
  return `La renta variable está ${points(plan.drift_equity)} ${side} del objetivo de tu plan.`;
}

/** Posiciones de dibujo (0–100) de la barra: no se muestran como cifra. */
function drawing(plan: PlanOut) {
  const pct = (s: string) => Number(s) * 100;
  const target = pct(plan.target.equity);
  const margin = pct(plan.drift_threshold);
  return { value: pct(plan.current.equity), target, band: [target - margin, target + margin] as const };
}

function Card({ children }: { children: ReactNode }) {
  return (
    <section aria-labelledby="plan-card-title" className="flex flex-col gap-4 rounded-card border border-line bg-surface p-5">
      <h3 id="plan-card-title" className="m-0 text-base font-medium text-ink-muted">
        Tu plan
      </h3>
      {children}
    </section>
  );
}

/**
 * «Tu plan»: el reparto actual de renta variable frente al objetivo y al margen que fijó el
 * usuario. Todo viene de `GET /portfolios/{id}/plan` (reparto, desviación y si supera el margen
 * los calcula el backend); aquí solo se formatea y se dibuja. Contexto, no órdenes.
 */
export function PlanCard({ portfolioId }: { portfolioId: string }) {
  const plan = usePlan(portfolioId);

  if (plan.isPending) {
    return (
      <div role="status" aria-label="Cargando tu plan" className="h-40 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse" />
    );
  }
  if (!plan.data) {
    return (
      <Card>
        <p className="m-0 text-base text-ink-muted">
          {isPlanMissing(plan.error)
            ? "Esta cartera aún no tiene un plan de inversión, así que no hay reparto con el que compararla."
            : "Ahora mismo no podemos mostrar tu plan. Vuelve a intentarlo en unos segundos."}
        </p>
      </Card>
    );
  }

  const p = plan.data;
  const d = drawing(p);
  const margin = formatWeight(p.drift_threshold);
  const current = formatPercent(p.current.equity);
  const target = formatWeight(p.target.equity);
  return (
    <Card>
      <ProgressBar
        label="Renta variable"
        value={d.value}
        target={d.target}
        band={d.band}
        valueText={`${current} hoy; objetivo del plan, ${target}`}
        valueNode={
          <Traced calcId={p.calc_id}>
            {current} hoy · objetivo {target}
          </Traced>
        }
        targetLabel={`La marca es tu objetivo; la zona sombreada, el margen de ±${margin} que fijaste.`}
      />
      <p className="m-0 text-base text-ink">{driftSentence(p)}</p>
      <p
        className={`m-0 inline-flex w-fit items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ${
          p.drift_exceeded ? "bg-atento-bg text-atento" : "bg-tranquilo-bg text-tranquilo"
        }`}
      >
        {p.drift_exceeded ? `Fuera del margen de ±${margin} de tu plan` : `Dentro del margen de ±${margin} de tu plan`}
      </p>
      <dl className="m-0 grid grid-cols-2 gap-3 border-t border-line pt-3 text-sm">
        <div>
          <dt className="text-ink-muted">Renta fija</dt>
          <dd className="m-0 tabular-nums text-ink">
            <Traced calcId={p.calc_id}>{formatPercent(p.current.fixed_income)}</Traced> · objetivo{" "}
            {formatWeight(p.target.fixed_income)}
          </dd>
        </div>
        <div>
          <dt className="text-ink-muted">Liquidez</dt>
          <dd className="m-0 tabular-nums text-ink">
            <Traced calcId={p.calc_id}>{formatPercent(p.current.cash)}</Traced> · objetivo{" "}
            {formatWeight(p.target.cash)}
          </dd>
        </div>
        {p.goal_amount_eur && p.goal_year && (
          <div className="col-span-2">
            <dt className="text-ink-muted">Meta del plan</dt>
            <dd className="m-0 tabular-nums text-ink">
              {formatEur(p.goal_amount_eur, 0)} en {p.goal_year}
            </dd>
          </div>
        )}
      </dl>
    </Card>
  );
}
