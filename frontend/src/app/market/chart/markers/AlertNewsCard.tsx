import { TraceLink } from "../../../../components/trace/TraceLink";
import { CATEGORY_LABEL } from "../../../news-feed/labels";
import { formatEurRange } from "../../../../lib/format";
import { pointDate } from "../chartFormat";
import { NewsCategoryIcon } from "./NewsCategoryIcon";
import { useActiveNewsMarker, type NewsMarkerStore } from "./newsMarkerStore";

export function AlertNewsCard({ store, id, width }: { store: NewsMarkerStore; id: string; width: number }) {
  const active = useActiveNewsMarker(store);
  const news = active?.marker.news;
  const estimate = news?.estimate;
  const cardWidth = Math.min(320, width || 320);
  const left = active ? Math.min(Math.max(active.x - cardWidth / 2, 0), Math.max(width - cardWidth, 0)) : 0;
  const above = (active?.y ?? 0) > 220;
  const compact = width < 400;
  const range =
    estimate &&
    (estimate.status === "estimated" || estimate.status === "measured") &&
    estimate.low_eur != null &&
    estimate.high_eur != null
      ? { low: estimate.low_eur, high: estimate.high_eur }
      : null;
  return (
    <div
      id={id}
      role="tooltip"
      hidden={!active}
      className="kchart-tip absolute z-40 flex flex-col gap-2 overflow-y-auto px-4 py-3 text-sm"
      style={{
        display: active ? undefined : "none",
        left,
        top: active ? active.y + (above ? -20 : 20) : 0,
        width: cardWidth,
        maxHeight: compact ? "13rem" : undefined,
        translate: above ? "0 -100%" : "0 0",
      }}
    >
      {active && news && (
        <>
          <div
            aria-hidden="true"
            className="relative -mx-4 -mt-3 mb-1 flex h-24 items-center justify-end overflow-hidden rounded-t-[11px] bg-primary-tint px-6"
          >
            <span className="absolute -right-5 -top-10 size-32 rounded-full border border-primary/20" />
            <span className="absolute right-4 top-1/2 size-20 -translate-y-1/2 rounded-full border border-primary/25" />
            <span className="relative grid size-14 place-items-center rounded-full bg-primary-tint-strong text-accent">
              <NewsCategoryIcon category={news.category} className="size-7" />
            </span>
          </div>
          <p className="m-0 text-base font-semibold leading-snug text-ink">{news.title}</p>
          <p className="m-0 flex items-center gap-1.5 text-xs font-semibold text-ink-muted">
            <NewsCategoryIcon category={news.category} />
            <span>{CATEGORY_LABEL[news.category]}</span>
            <span aria-hidden="true">·</span>
            <span>{pointDate(active.marker.marketDate)}</span>
          </p>
          <p className="m-0 line-clamp-3 text-ink-muted">{news.summary}</p>
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
                  {estimate.horizon_sessions && <p className="m-0 text-ink-muted">A {estimate.horizon_sessions} sesiones</p>}
                  <p className="m-0 text-xs text-ink-muted">
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
