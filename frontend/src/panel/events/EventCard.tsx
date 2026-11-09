import type { EventImpactOut, SurpriseLabel } from "../../api/generated/schema";
import { CONFIDENCE_LABEL, EVENT_TYPE_LABEL, POLARITY } from "../../app/news/labels";
import { ArrowRightIcon } from "../../components/icons";
import { formatDate } from "../../lib/format";
import { impactRange } from "../figures";
import { Traced } from "../Traced";

const SURPRISE_TEXT: Record<SurpriseLabel, string> = {
  mejor: "Mejor de lo esperado",
  peor: "Peor de lo esperado",
  en_linea: "En línea con lo esperado",
};

/**
 * Un evento que afecta a la cartera: cadena causal, impacto como rango con su confianza,
 * qué activos lo notan y de dónde viene. El impacto nunca es una cifra exacta (regla de
 * producto 5); el desglose por activo va sin importes porque el backend solo da estimaciones
 * puntuales ahí.
 */
export function EventCard({ event }: { event: EventImpactOut }) {
  const polarity = POLARITY[event.polarity];
  const surprise = event.surprise.label ? SURPRISE_TEXT[event.surprise.label] : null;
  const source = event.sources[0];
  return (
    <article
      id={`evento-${event.event_id}`}
      aria-labelledby={`evento-${event.event_id}-title`}
      className="scroll-mt-24 rounded-card border border-line bg-surface p-6"
    >
      <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-2">
        <div className="min-w-0">
          <p className="m-0 flex flex-wrap items-center gap-x-2 text-sm text-ink-muted">
            <span className="font-semibold text-accent">{EVENT_TYPE_LABEL[event.event_type]}</span>
            <span aria-hidden="true">·</span>
            <time dateTime={event.occurred_at}>{formatDate(event.occurred_at)}</time>
          </p>
          <h3
            id={`evento-${event.event_id}-title`}
            className="m-0 mt-1 text-balance text-xl font-semibold leading-snug text-ink"
          >
            {event.title}
          </h3>
        </div>
        <span className={`rounded-full px-3 py-1 text-sm font-semibold ${polarity.className}`}>
          {polarity.label}
        </span>
      </div>

      <ol
        aria-label="Cadena causal"
        className="m-0 mt-4 flex list-none flex-col items-start gap-1.5 p-0"
      >
        {event.causal_chain.map((step, i) => (
          <li key={step} className="flex items-start gap-2">
            <span aria-hidden="true" className="flex h-9 w-4 shrink-0 items-center justify-center">
              {i > 0 && <ArrowRightIcon className="size-4 text-ink-muted" />}
            </span>
            <span className="rounded-control bg-surface-muted px-3 py-1.5 text-base text-ink">
              {step}
            </span>
          </li>
        ))}
      </ol>

      <dl className="m-0 mt-5 flex flex-wrap items-end gap-x-8 gap-y-3">
        <div>
          <dt className="text-sm font-medium text-ink-muted">Impacto estimado en tu cartera</dt>
          <dd className="m-0 text-2xl font-semibold tabular-nums text-ink">
            <Traced calcId={event.calc_id}>{impactRange(event.low_eur, event.high_eur)}</Traced>
          </dd>
        </div>
        <div>
          <dt className="text-sm font-medium text-ink-muted">Fiabilidad</dt>
          <dd className="m-0 rounded-full bg-nodata-bg px-3 py-1 text-base font-semibold text-nodata">
            {CONFIDENCE_LABEL[event.confidence]}
          </dd>
        </div>
        {surprise && (
          <div>
            <dt className="text-sm font-medium text-ink-muted">Frente al consenso</dt>
            <dd className="m-0 text-base text-ink">{surprise}</dd>
          </div>
        )}
      </dl>

      {event.explanation && (
        <p className="m-0 mt-4 max-w-[65ch] text-base text-ink">{event.explanation}</p>
      )}

      {event.breakdown.length > 0 && (
        <details className="group mt-4">
          <summary className="inline-flex min-h-touch cursor-pointer items-center font-semibold text-accent underline">
            Qué activos lo notan ({event.breakdown.length})
          </summary>
          <ul className="m-0 mt-1 list-none p-0">
            {event.breakdown.map((b) => (
              <li
                key={b.asset_id}
                className="flex flex-wrap justify-between gap-x-4 border-b border-line py-2 text-base last:border-b-0"
              >
                <span className="text-ink">{b.name}</span>
                <span className="text-ink-muted">a través de {b.channel}</span>
              </li>
            ))}
          </ul>
        </details>
      )}

      {source && (
        <p className="m-0 mt-4 text-sm text-ink-muted">
          Fuente: {source.label}
          {source.as_of ? `, ${formatDate(source.as_of)}` : ""}
        </p>
      )}
    </article>
  );
}
