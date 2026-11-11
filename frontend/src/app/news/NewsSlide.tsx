import { Link } from "react-router";
import type { EventImpactOut } from "../../api/generated/schema";
import { ArrowRightIcon } from "../../components/icons";
import { TraceFigure } from "../../components/trace/TraceFigure";
import { formatDate, formatEurRange } from "../../lib/format";
import { CONFIDENCE_LABEL, EVENT_TYPE_LABEL, POLARITY } from "./labels";

interface NewsSlideProps {
  event: EventImpactOut;
  position: number;
  total: number;
  direction: "next" | "prev";
  panelHref: string;
}

/**
 * Texto de una noticia (la ilustración y los controles los pinta NewsCarousel a la izquierda).
 * Patrón de carrusel de WAI-ARIA: role="group" + aria-roledescription="noticia" + "2 de 3".
 * El impacto va como rango (nunca cifra exacta) y con su confianza; todo viene del backend.
 */
export function NewsSlide({ event, position, total, direction, panelHref }: NewsSlideProps) {
  const polarity = POLARITY[event.polarity];
  const summary = event.explanation ?? event.causal_chain.join(" → ");
  const source = event.sources[0];
  return (
    <div
      role="group"
      aria-roledescription="noticia"
      aria-label={`${position} de ${total}`}
      data-calc-id={event.calc_id}
      className={`h-full ${direction === "next" ? "motion-safe:animate-news-in-next" : "motion-safe:animate-news-in-prev"}`}
    >
      <div className="flex h-full min-w-0 flex-col gap-3">
        <p className="m-0 flex flex-wrap items-center gap-x-2 text-sm text-ink-muted">
          <span className="font-semibold text-accent">{EVENT_TYPE_LABEL[event.event_type]}</span>
          <span aria-hidden="true">·</span>
          <time dateTime={event.occurred_at}>{formatDate(event.occurred_at)}</time>
        </p>
        <h3 className="m-0 text-xl font-semibold leading-snug text-ink">{event.title}</h3>
        <p className="m-0 text-base text-ink-muted">{summary}</p>

        <dl className="m-0 mt-1 flex flex-wrap items-end gap-x-6 gap-y-3">
          <div>
            <dt className="text-sm font-medium text-ink-muted">Impacto estimado en tu cartera</dt>
            <dd className="m-0 text-lg font-semibold tabular-nums text-ink">
              <TraceFigure calcId={event.calc_id}>
                {formatEurRange(event.low_eur, event.high_eur)}
              </TraceFigure>
            </dd>
          </div>
          <div className="flex flex-wrap gap-2">
            <dt className="sr-only">Tipo de efecto</dt>
            <dd
              className={`m-0 rounded-full px-3 py-1 text-sm font-semibold ${polarity.className}`}
            >
              {polarity.label}
            </dd>
            <dt className="sr-only">Fiabilidad de la estimación</dt>
            <dd className="m-0 rounded-full bg-nodata-bg px-3 py-1 text-sm font-semibold text-nodata">
              {CONFIDENCE_LABEL[event.confidence]}
            </dd>
          </div>
        </dl>

        <div className="mt-auto flex flex-wrap items-center justify-between gap-x-4 gap-y-1 pt-2">
          {source && <p className="m-0 text-sm text-ink-muted">Fuente: {source.label}</p>}
          <Link
            to={panelHref}
            className="inline-flex min-h-touch items-center gap-1 font-semibold text-accent underline"
          >
            Ver en el panel
            <span className="sr-only">: {event.title}</span>
            <ArrowRightIcon className="size-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
