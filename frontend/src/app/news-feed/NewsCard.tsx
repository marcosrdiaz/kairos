import { useId } from "react";
import type { NewsItemOut, NewsPositionEstimate } from "../../api/generated/schema";
import { TraceFigure } from "../../components/trace/TraceFigure";
import { formatDate, formatEurRange } from "../../lib/format";
import { NewsEffect } from "./NewsEffect";
import { CATEGORY_LABEL, timingText } from "./labels";

/** Efecto por posición: rango y desde cuándo se nota (acciones en la sesión, fondos con el VL). */
function PositionEffects({
  positions,
  calcId,
}: {
  positions: NewsPositionEstimate[];
  calcId: string | null | undefined;
}) {
  if (positions.length === 0) return null;
  return (
    <div className="flex flex-col gap-2">
      <h4 className="m-0 text-sm font-semibold text-ink">En tus posiciones</h4>
      <ul className="m-0 flex list-none flex-col gap-2 p-0">
        {positions.map((p) => (
          <li
            key={p.asset_id}
            className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-t border-line pt-2"
          >
            <span className="font-medium text-ink">{p.name}</span>
            <span className="tabular-nums text-ink">
              <TraceFigure calcId={calcId}>{formatEurRange(p.low_eur, p.high_eur)}</TraceFigure>
            </span>
            <span className="w-full text-sm text-ink-muted">
              {timingText(p.timing, p.effective_from)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Una noticia vista desde la cartera elegida. Empieza por lo que significa para la cartera
 * (`kairos-spec.md`: sin noticias en bruto); debajo, el titular, por qué afecta y la fuente.
 */
export function NewsCard({ item }: { item: NewsItemOut }) {
  const titleId = useId();
  const estimate = item.estimate;
  return (
    <article
      aria-labelledby={titleId}
      className="flex flex-col gap-4 rounded-card border border-line bg-surface p-5"
    >
      <NewsEffect estimate={estimate} />

      <div className="flex flex-col gap-1 border-t border-line pt-4">
        <p className="m-0 flex flex-wrap items-center gap-x-2 text-sm text-ink-muted">
          <span className="font-semibold text-accent">{CATEGORY_LABEL[item.category]}</span>
          <span aria-hidden="true">·</span>
          <time dateTime={item.published_at}>{formatDate(item.published_at)}</time>
        </p>
        <h3 id={titleId} className="m-0 text-xl font-semibold leading-snug text-ink">
          {item.title}
        </h3>
        <p className="m-0 max-w-[65ch] text-base text-ink-muted">{item.summary}</p>
      </div>

      {item.causal_chain.length > 0 && (
        <div className="flex flex-col gap-2">
          <h4 className="m-0 text-sm font-semibold text-ink">Por qué te afecta</h4>
          <ol className="m-0 flex list-decimal flex-col gap-1 pl-5 text-base text-ink-muted">
            {item.causal_chain.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      {estimate && <PositionEffects positions={estimate.positions ?? []} calcId={estimate.calc_id} />}

      <p className="m-0 text-sm text-ink-muted">
        Fuente:{" "}
        {item.source.url ? (
          <a
            href={item.source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-accent underline"
          >
            {item.source.label}
            <span className="sr-only"> (se abre en otra pestaña)</span>
          </a>
        ) : (
          item.source.label
        )}
      </p>
    </article>
  );
}
