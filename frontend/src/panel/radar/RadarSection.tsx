import type { RadarItem, RadarKind } from "../../api/generated/schema";
import { useRadar } from "../../api/hooks/useRadar";
import { EmptyNote } from "../../components/PageTitle";
import { formatEur } from "../../lib/format";
import { PanelSection } from "../PanelSection";
import { Traced } from "../Traced";

const TITLE = "Radar";
const INTRO =
  "Riesgos y oportunidades de tu cartera, siempre frente a tus propias reglas. Es contexto, no una orden.";

/** Riesgo en ámbar y oportunidad en verde (sin rojo), siempre con la palabra. */
const KIND: Record<RadarKind, { label: string; className: string }> = {
  risk: { label: "Riesgo", className: "bg-atento-bg text-atento" },
  opportunity: { label: "Oportunidad", className: "bg-tranquilo-bg text-tranquilo" },
};

const RULE_SOURCE = { dca_plan: "tu plan de aportaciones", plan: "tu plan" } as const;

function RadarCard({ item }: { item: RadarItem }) {
  const kind = KIND[item.kind];
  return (
    <li className="rounded-card border border-line bg-surface p-6" data-rule={item.rule}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="m-0 max-w-[40ch] text-balance text-xl font-semibold leading-snug text-ink">
          {item.title}
        </h3>
        <span className={`rounded-full px-3 py-1 text-sm font-semibold ${kind.className}`}>
          {kind.label}
        </span>
      </div>
      <p className="m-0 mt-3 max-w-[65ch] text-base text-ink">{item.detail}</p>
      <dl className="m-0 mt-4 flex flex-wrap gap-x-8 gap-y-2">
        {item.value_eur && (
          <div>
            <dt className="text-sm font-medium text-ink-muted">Importe implicado</dt>
            <dd className="m-0 text-lg font-semibold tabular-nums text-ink">
              <Traced calcId={item.calc_id}>{formatEur(item.value_eur, 0)}</Traced>
            </dd>
          </div>
        )}
        {item.user_rule && (
          <div>
            <dt className="text-sm font-medium text-ink-muted">Frente a</dt>
            <dd className="m-0 text-lg text-ink">{RULE_SOURCE[item.user_rule.source]}</dd>
          </div>
        )}
      </dl>
    </li>
  );
}

/** Radar: lo que sale es lo que el backend detecta con sus 6 reglas; sin nada, se dice. */
export function RadarSection({ portfolioId }: { portfolioId: string }) {
  const { data, isPending } = useRadar(portfolioId);

  return (
    <PanelSection id="radar" title={TITLE} intro={INTRO} step={3}>
      {isPending && (
        <div
          role="status"
          aria-label="Cargando el radar"
          className="h-32 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse"
        />
      )}
      {!isPending && !data && (
        <EmptyNote>
          Ahora mismo no podemos mostrar el radar. Vuelve a intentarlo en unos segundos.
        </EmptyNote>
      )}
      {data && data.items.length === 0 && (
        <EmptyNote>
          Ahora mismo el radar no ve riesgos ni oportunidades que destacar en tu cartera.
        </EmptyNote>
      )}
      {data && data.items.length > 0 && (
        <ul className="m-0 flex list-none flex-col gap-4 p-0">
          {data.items.map((item) => (
            <RadarCard key={item.id} item={item} />
          ))}
        </ul>
      )}
    </PanelSection>
  );
}
