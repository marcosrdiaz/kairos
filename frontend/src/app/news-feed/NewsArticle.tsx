import { useId, useLayoutEffect, useRef, useState } from "react";
import type { NewsItemOut, NewsPositionEstimate } from "../../api/generated/schema";
import { TraceFigure } from "../../components/trace/TraceFigure";
import { NewsCover } from "./NewsCover";
import { NewsEffect } from "./NewsEffect";
import { eurRangeText, timingText } from "./labels";

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
              <TraceFigure calcId={calcId}>{eurRangeText(p.low_eur, p.high_eur)}</TraceFigure>
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
 * Texto de la noticia recortado a unas líneas con un fundido abajo y «Mostrar más». El botón solo
 * sale si el texto de verdad no cabe; el texto completo siempre está en el DOM.
 */
function ClampedText({ text }: { text: string }) {
  const ref = useRef<HTMLParagraphElement>(null);
  const [overflows, setOverflows] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const textId = useId();

  useLayoutEffect(() => {
    const el = ref.current;
    if (el && !expanded) setOverflows(el.scrollHeight > el.clientHeight + 1);
  }, [text, expanded]);

  const clamped = !expanded && overflows;
  return (
    <div className="flex flex-col items-start gap-2">
      <div className="relative">
        <p
          id={textId}
          ref={ref}
          className={`m-0 max-w-[65ch] text-base text-ink-muted ${expanded ? "" : "line-clamp-4"}`}
        >
          {text}
        </p>
        {clamped && (
          <span
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-surface to-transparent"
          />
        )}
      </div>
      {overflows && (
        <button
          type="button"
          aria-expanded={expanded}
          aria-controls={textId}
          onClick={() => setExpanded((v) => !v)}
          className="min-h-touch cursor-pointer border-0 bg-transparent p-0 text-base font-semibold text-accent underline underline-offset-4"
        >
          {expanded ? "Mostrar menos" : "Mostrar más"}
        </button>
      )}
    </div>
  );
}

/**
 * Una noticia completa vista desde la cartera elegida (detalle de T5-17): portada, titular,
 * texto recortado y «Cómo afecta a tu cartera» con el efecto, por qué afecta, las posiciones y la
 * fuente. Todas las cifras vienen del backend con su `calc_id`.
 */
export function NewsArticle({ item, titleId }: { item: NewsItemOut; titleId?: string }) {
  const ownId = useId();
  const headingId = titleId ?? ownId;
  const estimate = item.estimate;
  return (
    <article aria-labelledby={headingId} className="flex flex-col gap-5">
      <NewsCover category={item.category} publishedAt={item.published_at} large />
      <h3 id={headingId} className="m-0 text-2xl font-semibold leading-snug text-ink">
        {item.title}
      </h3>
      <ClampedText text={item.summary} />

      <section
        aria-labelledby={`${headingId}-efecto`}
        className="flex flex-col gap-4 border-t border-line pt-5"
      >
        <h4 id={`${headingId}-efecto`} className="m-0 text-lg font-semibold text-ink">
          Cómo afecta a tu cartera
        </h4>
        <NewsEffect estimate={estimate} />
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
        {estimate && (
          <PositionEffects positions={estimate.positions ?? []} calcId={estimate.calc_id} />
        )}
      </section>

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
