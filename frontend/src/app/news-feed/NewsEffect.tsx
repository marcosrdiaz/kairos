import type { Confidence, NewsEstimateOut, NewsEstimateStatus } from "../../api/generated/schema";
import { ArrowDownIcon, ArrowUpIcon } from "../../components/icons";
import { TraceFigure } from "../../components/trace/TraceFigure";
import { CONFIDENCE_LABEL, POLARITY } from "../news/labels";
import { STATUS_LABEL, horizonText, methodText, rangeTexts } from "./labels";

const PILL = "m-0 rounded-full px-3 py-1 text-sm font-semibold";
const STATUS_TONE: Record<NewsEstimateStatus, string> = {
  estimated: "bg-icon-gold-bg text-icon-gold",
  measured: "bg-icon-green-bg text-icon-green",
  pending: "bg-icon-blue-bg text-icon-blue",
  not_relevant: "bg-nodata-bg text-nodata",
};
const CONFIDENCE_TONE: Record<Confidence, string> = {
  alta: "bg-icon-green-bg text-icon-green",
  media: "bg-icon-blue-bg text-icon-blue",
  baja: "bg-icon-gold-bg text-icon-gold",
};

/**
 * Lo primero de cada noticia: qué puede significar para la cartera elegida. Todas las cifras
 * vienen del backend (motor de impacto); aquí solo se formatean. Siempre en rango, con su
 * etiqueta «Estimado» o «Medido», la confianza y de dónde sale. `compact` (cards de la lista):
 * la misma frase con su rango y sus etiquetas, sin el porcentaje ni el método, que van al detalle.
 */
export function NewsEffect({
  estimate,
  compact = false,
}: {
  estimate: NewsEstimateOut | null;
  compact?: boolean;
}) {
  const sentence = compact
    ? "m-0 text-base font-semibold text-ink"
    : "m-0 text-lg font-semibold text-ink";
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
  const MovementIcon =
    estimate.polarity === "riesgo"
      ? ArrowDownIcon
      : estimate.polarity === "oportunidad"
        ? ArrowUpIcon
        : null;
  const movementTone =
    estimate.polarity === "riesgo"
      ? "text-trend-down"
      : estimate.polarity === "oportunidad"
        ? "text-trend-up"
        : "text-ink";
  const method = methodText(estimate);
  return (
    <div className="flex flex-col gap-2">
      <dl className="m-0 flex flex-wrap gap-2">
        {polarity && (
          <>
            <dt className="sr-only">Tipo de efecto</dt>
            <dd
              data-news-polarity={estimate.polarity}
              className={`${PILL} ${polarity.className}`}
            >
              {polarity.label}
            </dd>
          </>
        )}
        <dt className="sr-only">Tipo de cifra</dt>
        <dd
          data-news-status={estimate.status}
          className={`${PILL} ${STATUS_TONE[estimate.status]}`}
        >
          {STATUS_LABEL[estimate.status]}
        </dd>
        {estimate.confidence && (
          <>
            <dt className="sr-only">Fiabilidad de la estimación</dt>
            <dd className={`${PILL} ${CONFIDENCE_TONE[estimate.confidence]}`}>
              {CONFIDENCE_LABEL[estimate.confidence]}
            </dd>
          </>
        )}
      </dl>
      {estimate.status === "measured" ? (
        <p className={sentence}>
          Ese día tu cartera se movió{" "}
          <span className="tabular-nums">
            {MovementIcon && (
              <MovementIcon
                aria-hidden="true"
                className={`mr-1 inline size-4 ${movementTone}`}
              />
            )}
            <TraceFigure calcId={estimate.calc_id}>
              <span data-news-value-tone={estimate.polarity} className={movementTone}>
                {ranges.eur}
              </span>
            </TraceFigure>
          </span>{" "}
          por esta vía.
        </p>
      ) : (
        <p className={sentence}>
          Tu cartera podría moverse{" "}
          <span className="tabular-nums">
            {MovementIcon && (
              <MovementIcon
                aria-hidden="true"
                className={`mr-1 inline size-4 ${movementTone}`}
              />
            )}
            <TraceFigure calcId={estimate.calc_id}>
              <span data-news-value-tone={estimate.polarity} className={movementTone}>
                {ranges.eur}
              </span>
            </TraceFigure>
          </span>{" "}
          {horizonText(estimate.horizon_sessions)}.
        </p>
      )}
      {!compact && (
        <p className="m-0 text-sm text-ink-muted">
          Equivale a <span className="tabular-nums">{ranges.pct}</span> del valor de la cartera.
          {method && ` ${method}.`}
        </p>
      )}
    </div>
  );
}
