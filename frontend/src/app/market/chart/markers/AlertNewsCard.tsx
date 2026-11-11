import { TraceLink } from "../../../../components/trace/TraceLink";
import { formatEurRange } from "../../../../lib/format";
import { pointDate } from "../chartFormat";
import { useActiveNewsMarker, type NewsMarkerStore } from "./newsMarkerStore";

export function AlertNewsCard({ store, id, width }: { store: NewsMarkerStore; id: string; width: number }) {
  const active = useActiveNewsMarker(store);
  const news = active?.marker.news;
  const estimate = news?.estimate;
  const cardWidth = Math.min(320, width || 320);
  const left = active ? Math.min(Math.max(active.x - cardWidth / 2, 0), Math.max(width - cardWidth, 0)) : 0;
  const above = (active?.y ?? 0) > 220;
  return (
    <div
      id={id}
      role="tooltip"
      hidden={!active}
      className="kchart-tip absolute z-30 flex flex-col gap-2 px-4 py-3 text-sm"
      style={{ display: active ? undefined : "none", left, top: active ? active.y + (above ? -20 : 20) : 0, width: cardWidth, translate: above ? "0 -100%" : "0 0" }}
    >
      {active && news && (
        <>
          <p className="m-0 text-xs font-semibold uppercase tracking-wider text-brand-red">
            Noticia con aviso · {pointDate(active.marker.marketDate)}
          </p>
          <p className="m-0 text-base font-semibold leading-snug text-ink">{news.title}</p>
          <p className="m-0 line-clamp-3 text-ink-muted">{news.summary}</p>
          {estimate && estimate.low_eur && estimate.high_eur && (
            <div className="border-t border-line pt-2" data-calc-id={estimate.calc_id ?? undefined}>
              <p className="m-0 font-semibold text-ink">
                {estimate.status === "measured" ? "Impacto medido" : "Impacto estimado"} en tu cartera
              </p>
              <p className="m-0 tabular-nums text-ink">{formatEurRange(estimate.low_eur, estimate.high_eur)}</p>
              {estimate.horizon_sessions && <p className="m-0 text-ink-muted">A {estimate.horizon_sessions} sesiones</p>}
              <TraceLink calcId={estimate.calc_id} className="text-sm" />
            </div>
          )}
        </>
      )}
    </div>
  );
}
