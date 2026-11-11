import { useState } from "react";
import type { HistoryPeriod, PortfolioOut } from "../../api/generated/schema";
import { usePortfolioHistory } from "../../api/hooks/usePortfolioHistory";
import { PERIODS } from "../../app/market/chart/chartFormat";
import { formatDate, formatEur } from "../../lib/format";
import { MetricCard } from "../../ui/MetricCard";
import { signedPercent, trendOf } from "../../widget/states";
import { signedEur } from "../figures";
import { Traced } from "../Traced";

const TREND_CLASS = { up: "text-trend-up", down: "text-trend-down", flat: "text-ink-muted" };
const TREND_ARROW = { up: "▲", down: "▼", flat: "■" };
const OPTIONS = PERIODS.map((p) => ({ id: p.value, label: p.label, name: p.name }));
const isZero = (v: string) => /^[+-]?0*(\.0*)?$/.test(v.trim());

/** Contexto del periodo: valor al empezar y dinero aportado o retirado (no es rentabilidad). */
function PeriodDetail({ portfolioId, period }: { portfolioId: string; period: HistoryPeriod }) {
  const history = usePortfolioHistory(portfolioId, period);
  if (history.isPending) return <span>Cargando la evolución del periodo…</span>;
  const h = history.data;
  if (!h || h.points.length === 0) return <span>No hay evolución disponible para este periodo.</span>;
  return (
    <>
      Al empezar el periodo:{" "}
      <span className="font-semibold tabular-nums text-ink">
        <Traced calcId={h.calc_id}>{formatEur(h.start_value_eur)}</Traced>
      </span>
      {" · "}
      {isZero(h.net_flows_eur) ? (
        "sin aportaciones ni retiradas."
      ) : (
        <>
          {h.net_flows_eur.trim().startsWith("-") ? "retiradas: " : "aportaciones: "}
          <span className="font-semibold tabular-nums text-ink">
            <Traced calcId={h.calc_id}>{signedEur(h.net_flows_eur)}</Traced>
          </span>{" "}
          (dinero que entró o salió, no rentabilidad).
        </>
      )}
    </>
  );
}

/**
 * Patrimonio como tarjeta de cifra con periodos (T5-02). La cifra y la variación semanal salen de
 * `/portfolios/{id}`; la línea y el contexto del periodo, de `/portfolios/{id}/history?period=`.
 * Nada se calcula aquí: la serie solo se convierte a número para dibujarla.
 */
export function WealthCard({
  portfolioId,
  portfolio,
  eventTitles,
}: {
  portfolioId: string;
  portfolio: PortfolioOut;
  eventTitles: Map<string, string>;
}) {
  const [period, setPeriod] = useState<HistoryPeriod>("1m");
  const history = usePortfolioHistory(portfolioId, period);
  const series = (history.data?.points ?? []).map((pt) => Number(pt.value_eur));
  const name = PERIODS.find((p) => p.value === period)?.name ?? period;
  const p = portfolio;
  const trend = trendOf(p.change_week_pct);

  return (
    <MetricCard
      className="h-full rounded-none border-0 bg-transparent p-6"
      label="Patrimonio"
      periods={OPTIONS}
      activeId={period}
      onPeriodChange={(id) => setPeriod(id as HistoryPeriod)}
      value={<Traced calcId={p.calc_id}>{formatEur(p.total_eur)}</Traced>}
      detail={`Valorado a ${formatDate(p.valued_at)}`}
      series={series}
      seriesLabel={`Evolución del valor de la cartera: ${name.toLowerCase()}`}
      busy={history.isPlaceholderData}
      periodDetail={<PeriodDetail portfolioId={portfolioId} period={period} />}
    >
      <dl className="m-0 mt-4 grid gap-3 border-t border-line pt-3">
        <div>
          <dt className="text-sm font-medium text-ink-muted">Última semana</dt>
          <dd className={`m-0 mt-1 text-xl font-semibold tabular-nums ${TREND_CLASS[trend]}`}>
            <span aria-hidden="true" className="mr-1 text-sm">
              {TREND_ARROW[trend]}
            </span>
            <Traced calcId={p.calc_id}>{signedEur(p.change_week_eur)}</Traced>{" "}
            <span className="text-sm text-ink-muted">({signedPercent(p.change_week_pct)})</span>
          </dd>
        </div>
        {p.demo_adjustments?.map((a) => (
          <div key={a.calc_id}>
            <dt className="text-sm font-medium text-ink-muted">Ajuste de demostración</dt>
            <dd className={`m-0 text-base ${TREND_CLASS[trendOf(a.impact_eur)]}`}>
              {eventTitles.get(a.event_id) ?? a.label}:{" "}
              <span className="tabular-nums">
                <Traced calcId={a.calc_id}>{signedEur(a.impact_eur)}</Traced>
              </span>
            </dd>
          </div>
        ))}
      </dl>
    </MetricCard>
  );
}
