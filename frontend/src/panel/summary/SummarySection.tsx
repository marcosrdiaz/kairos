import { useEvents } from "../../api/hooks/useEvents";
import { useLivePortfolio } from "../../api/hooks/useLivePortfolio";
import { useStatus } from "../../api/hooks/useStatus";
import { EmptyNote } from "../../components/PageTitle";
import { formatDate, formatEur } from "../../lib/format";
import { signedPercent, trendOf, withoutTapHint } from "../../widget/states";
import { StatusBadge } from "../../widget/StatusBadge";
import { signedEur } from "../figures";
import { PanelSection } from "../PanelSection";
import { Traced } from "../Traced";
import { PositionsTable } from "./PositionsTable";

const TREND_CLASS = { up: "text-trend-up", down: "text-trend-down", flat: "text-ink-muted" };
const TREND_ARROW = { up: "▲", down: "▼", flat: "■" };

function SummarySkeleton() {
  return (
    <div role="status" aria-label="Cargando el resumen" className="flex flex-col gap-4">
      <div className="h-40 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse" />
      <div className="h-64 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse" />
    </div>
  );
}

/**
 * Resumen: estado y frase del día, patrimonio y variación de la semana, y las posiciones.
 * El patrimonio y las posiciones son cifras exactas con la fecha del precio; todo viene del
 * backend (`/status` y `/portfolios/{id}`), aquí solo se formatea.
 */
export function SummarySection({ portfolioId }: { portfolioId: string }) {
  const status = useStatus(portfolioId);
  const portfolio = useLivePortfolio(portfolioId);
  const events = useEvents(portfolioId);

  if (status.isPending || portfolio.isPending) {
    return (
      <PanelSection id="resumen" title="Resumen" step={0}>
        <SummarySkeleton />
      </PanelSection>
    );
  }
  if (!portfolio.data) {
    return (
      <PanelSection id="resumen" title="Resumen" step={0}>
        <EmptyNote>
          Ahora mismo no podemos mostrar tu cartera. Vuelve a intentarlo en unos segundos.
        </EmptyNote>
      </PanelSection>
    );
  }

  const p = portfolio.data;
  // El ajuste solo trae `event_id`: el título sale de los eventos (misma caché que el bloque Eventos).
  const eventTitles = new Map((events.data ?? []).map((e) => [e.event_id, e.title]));
  const trend = trendOf(p.change_week_pct);
  return (
    <PanelSection
      id="resumen"
      title="Resumen"
      intro="Cómo está tu cartera hoy, con los precios de cierre más recientes."
      step={0}
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
        <div className="flex flex-col items-start gap-4 rounded-card border border-line bg-surface p-6">
          {status.data ? (
            <>
              <div aria-live="polite" aria-atomic="true">
                <StatusBadge state={status.data.state} label={status.data.state_label} />
              </div>
              <p className="m-0 max-w-[30ch] text-2xl font-semibold leading-snug text-ink">
                <Traced calcId={status.data.calc_id}>{withoutTapHint(status.data.sentence)}</Traced>
              </p>
            </>
          ) : (
            <p className="m-0 text-base text-ink-muted">
              No podemos mostrar el estado ahora mismo; las cifras de abajo siguen siendo válidas.
            </p>
          )}
        </div>

        <dl className="m-0 grid grid-cols-2 gap-4 rounded-card border border-line bg-surface p-6">
          <div>
            <dt className="text-base font-medium text-ink-muted">Patrimonio</dt>
            <dd className="m-0 mt-1 text-3xl font-semibold tabular-nums text-ink">
              <Traced calcId={p.calc_id}>{formatEur(p.total_eur)}</Traced>
            </dd>
            <dd className="m-0 mt-1 text-sm text-ink-muted">
              Valorado a {formatDate(p.valued_at)}
            </dd>
          </div>
          <div>
            <dt className="text-base font-medium text-ink-muted">Última semana</dt>
            <dd className={`m-0 mt-1 text-3xl font-semibold tabular-nums ${TREND_CLASS[trend]}`}>
              <span aria-hidden="true" className="mr-1 text-base">
                {TREND_ARROW[trend]}
              </span>
              <Traced calcId={p.calc_id}>{signedEur(p.change_week_eur)}</Traced>
            </dd>
            <dd className="m-0 mt-1 text-sm tabular-nums text-ink-muted">
              {signedPercent(p.change_week_pct)}
            </dd>
          </div>
          {p.demo_adjustments?.map((a) => (
            <div key={a.calc_id} className="col-span-2 border-t border-line pt-3">
              <dt className="text-sm font-medium text-ink-muted">Ajuste de demostración</dt>
              <dd className="m-0 text-base text-ink">
                {eventTitles.get(a.event_id) ?? a.label}:{" "}
                <span className="tabular-nums">
                  <Traced calcId={a.calc_id}>{signedEur(a.impact_eur)}</Traced>
                </span>
              </dd>
            </div>
          ))}
        </dl>
      </div>

      <PositionsTable portfolio={p} />
    </PanelSection>
  );
}
