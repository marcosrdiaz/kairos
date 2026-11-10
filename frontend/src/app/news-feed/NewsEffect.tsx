import type { NewsEstimateOut } from "../../api/generated/schema";
import { TraceFigure } from "../../components/trace/TraceFigure";
import { CONFIDENCE_LABEL, POLARITY } from "../news/labels";
import { STATUS_LABEL, horizonText, methodText, rangeTexts } from "./labels";

const PILL = "m-0 rounded-full px-3 py-1 text-sm font-semibold";

/**
 * Lo primero de cada noticia: qué puede significar para la cartera elegida. Todas las cifras
 * vienen del backend (motor de impacto); aquí solo se formatean. Siempre en rango, con su
 * etiqueta «Estimado» o «Medido», la confianza y de dónde sale.
 */
export function NewsEffect({ estimate }: { estimate: NewsEstimateOut | null }) {
  if (!estimate) {
    return <p className="m-0 text-base text-ink-muted">Todavía estamos analizando esta noticia.</p>;
  }
  if (estimate.status === "not_relevant") {
    return <p className="m-0 text-base text-ink-muted">No afecta a tu cartera.</p>;
  }
  const ranges = rangeTexts(estimate);
  if (estimate.status === "pending" || !ranges || !estimate.horizon_sessions) {
    return (
      <p className="m-0 text-base text-ink-muted">
        Afecta a tu cartera. Estamos calculando cuánto podría moverla.
      </p>
    );
  }
  const polarity = estimate.polarity ? POLARITY[estimate.polarity] : null;
  const method = methodText(estimate);
  return (
    <div className="flex flex-col gap-2">
      <dl className="m-0 flex flex-wrap gap-2">
        {polarity && (
          <>
            <dt className="sr-only">Tipo de efecto</dt>
            <dd className={`${PILL} ${polarity.className}`}>{polarity.label}</dd>
          </>
        )}
        <dt className="sr-only">Tipo de cifra</dt>
        <dd className={`${PILL} border border-line text-ink`}>{STATUS_LABEL[estimate.status]}</dd>
        {estimate.confidence && (
          <>
            <dt className="sr-only">Fiabilidad de la estimación</dt>
            <dd className={`${PILL} bg-nodata-bg text-nodata`}>
              {CONFIDENCE_LABEL[estimate.confidence]}
            </dd>
          </>
        )}
      </dl>
      {estimate.status === "measured" ? (
        <p className="m-0 text-lg font-semibold text-ink">
          Ese día tu cartera se movió{" "}
          <span className="tabular-nums">
            <TraceFigure calcId={estimate.calc_id}>{ranges.eur}</TraceFigure>
          </span>{" "}
          por esta vía.
        </p>
      ) : (
        <p className="m-0 text-lg font-semibold text-ink">
          Tu cartera podría moverse{" "}
          <span className="tabular-nums">
            <TraceFigure calcId={estimate.calc_id}>{ranges.eur}</TraceFigure>
          </span>{" "}
          {horizonText(estimate.horizon_sessions)}.
        </p>
      )}
      <p className="m-0 text-sm text-ink-muted">
        Equivale a <span className="tabular-nums">{ranges.pct}</span> del valor de la cartera.
        {method && ` ${method}.`}
      </p>
    </div>
  );
}
