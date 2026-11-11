import { useEvents } from "../../api/hooks/useEvents";
import { useLivePortfolio } from "../../api/hooks/useLivePortfolio";
import { useStatus } from "../../api/hooks/useStatus";
import { EmptyNote } from "../../components/PageTitle";
import { TextMorph } from "../../ui/TextMorph";
import { withoutTapHint } from "../../widget/states";
import { StatusBadge } from "../../widget/StatusBadge";
import { PanelSection } from "../PanelSection";
import { Traced } from "../Traced";
import { PlanCard } from "./PlanCard";
import { PositionsTable } from "./PositionsTable";
import { WealthCard } from "./WealthCard";

function SummarySkeleton() {
  return (
    <div role="status" aria-label="Cargando el resumen" className="flex flex-col gap-4">
      <div className="h-40 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse" />
      <div className="h-64 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse" />
    </div>
  );
}

/**
 * Resumen: estado y frase del día, patrimonio con periodos, «Tu plan» y las posiciones.
 * El patrimonio y las posiciones son cifras exactas con la fecha del precio; todo viene del
 * backend (`/status`, `/portfolios/{id}`, `/history` y `/plan`), aquí solo se formatea.
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
  return (
    <PanelSection
      id="resumen"
      title="Resumen"
      intro="Cómo está tu cartera hoy, con los precios de cierre más recientes."
      step={0}
    >
      <div className="overflow-hidden rounded-card border border-line bg-surface">
        <div className="flex flex-col items-start gap-4 p-6">
          {status.data ? (
            <>
              <div aria-live="polite" aria-atomic="true">
                <StatusBadge state={status.data.state} label={status.data.state_label} />
              </div>
              <p className="m-0 max-w-[40ch] text-2xl font-semibold leading-snug text-ink">
                <Traced calcId={status.data.calc_id}>
                  <TextMorph text={withoutTapHint(status.data.sentence)} />
                </Traced>
              </p>
            </>
          ) : (
            <p className="m-0 text-base text-ink-muted">
              No podemos mostrar el estado ahora mismo; las cifras de abajo siguen siendo válidas.
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 items-stretch divide-y divide-line border-t border-line lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] lg:divide-x lg:divide-y-0">
          <WealthCard portfolioId={portfolioId} portfolio={p} eventTitles={eventTitles} />
          <PlanCard portfolioId={portfolioId} />
        </div>
      </div>

      <PositionsTable portfolio={p} />
    </PanelSection>
  );
}
