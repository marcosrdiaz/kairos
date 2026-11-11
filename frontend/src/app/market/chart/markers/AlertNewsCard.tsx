import { useLayoutEffect, useRef, useState } from "react";
import { TraceLink } from "../../../../components/trace/TraceLink";
import { CATEGORY_LABEL, sessionsText } from "../../../news-feed/labels";
import { formatEurRange } from "../../../../lib/format";
import { pointDate } from "../chartFormat";
import { NewsCategoryIcon } from "./NewsCategoryIcon";
import { useActiveNewsMarker, type NewsMarkerStore } from "./newsMarkerStore";

const GAP = 20; // distancia entre el punto y la tarjeta
const EDGE = 4; // margen mínimo con el borde del contenedor

/**
 * Tarjeta de una noticia con aviso. `height` es la altura del contenedor de la gráfica: con ella la
 * tarjeta se mide y se coloca dentro (debajo del punto si cabe y, si no, encima), de modo que no
 * tape la leyenda ni la tabla de debajo. Sin `height` (tests) usa la regla simple de arriba/abajo.
 */
export function AlertNewsCard({ store, id, width, height = 0 }: { store: NewsMarkerStore; id: string; width: number; height?: number }) {
  const active = useActiveNewsMarker(store);
  const ref = useRef<HTMLDivElement>(null);
  const [fitTop, setFitTop] = useState<number | null>(null);
  useLayoutEffect(() => {
    if (!active || !height || !ref.current) return setFitTop(null);
    const h = ref.current.offsetHeight;
    const below = active.y + GAP;
    const desired = below + h <= height - EDGE ? below : active.y - GAP - h;
    setFitTop(Math.min(Math.max(desired, EDGE), Math.max(height - h - EDGE, EDGE)));
  }, [active, height]);
  const news = active?.marker.news;
  const estimate = news?.estimate;
  const cardWidth = Math.min(320, width || 320);
  const left = active ? Math.min(Math.max(active.x - cardWidth / 2, 0), Math.max(width - cardWidth, 0)) : 0;
  const above = (active?.y ?? 0) > 220;
  const compact = width < 400;
  const maxHeight = `${compact ? 15 : 21}rem`;
  const range =
    estimate &&
    (estimate.status === "estimated" || estimate.status === "measured") &&
    estimate.low_eur != null &&
    estimate.high_eur != null
      ? { low: estimate.low_eur, high: estimate.high_eur }
      : null;
  return (
    <div
      ref={ref}
      id={id}
      role="tooltip"
      hidden={!active}
      className="kchart-tip absolute z-40 flex flex-col gap-1.5 overflow-y-auto px-4 py-2.5 text-sm"
      style={{
        display: active ? undefined : "none",
        left,
        top: !active ? 0 : fitTop ?? active.y + (above ? -GAP : GAP),
        width: cardWidth,
        maxHeight: height ? `min(${maxHeight}, ${height - 2 * EDGE}px)` : compact ? "13rem" : undefined,
        translate: fitTop === null && above ? "0 -100%" : "0 0",
      }}
    >
      {active && news && (
        <>
          <p className="m-0 line-clamp-2 shrink-0 text-base font-semibold leading-snug text-ink">{news.title}</p>
          <p className="m-0 flex items-center gap-1.5 text-xs font-semibold text-ink-muted">
            <NewsCategoryIcon category={news.category} />
            <span>{CATEGORY_LABEL[news.category]}</span>
            <span aria-hidden="true">·</span>
            <span>{pointDate(active.marker.marketDate)}</span>
          </p>
          <p className={`m-0 line-clamp-1 shrink-0 text-ink-muted${compact ? " hidden" : ""}`}>{news.summary}</p>
          {estimate && (
            <div className="border-t border-line pt-2" data-calc-id={estimate.calc_id ?? undefined}>
              <p className="m-0 font-semibold text-ink">
                {estimate.status === "measured"
                  ? "Impacto medido en tu cartera"
                  : estimate.status === "estimated"
                    ? "Impacto estimado en tu cartera"
                    : estimate.status === "pending"
                      ? "Impacto en tu cartera pendiente de medición"
                      : "Sin impacto estimado para tu cartera"}
              </p>
              {range ? (
                <>
                  <p className="m-0 tabular-nums text-ink">{formatEurRange(range.low, range.high)}</p>
                  {estimate.horizon_sessions && <p className="m-0 text-ink-muted">A {sessionsText(estimate.horizon_sessions)}</p>}
                  <p className={`m-0 text-xs text-ink-muted${compact ? " hidden" : ""}`}>
                    El movimiento medido del mercado no está disponible; se muestra el impacto en tu cartera.
                  </p>
                </>
              ) : (
                <p className="m-0 text-ink-muted">No se muestran cifras porque no hay un rango disponible.</p>
              )}
              <TraceLink calcId={estimate.calc_id} className="text-sm" />
            </div>
          )}
        </>
      )}
    </div>
  );
}
