import type { KeyboardEvent } from "react";
import { formatEurRange } from "../../../../lib/format";
import { pointDate } from "../chartFormat";
import type { NewsMarkerStore } from "./newsMarkerStore";
import type { AlertNewsMarker } from "./useAlertNewsMarkers";

export function AlertNewsDot({ cx, cy, marker, store, cardId }: {
  cx?: number;
  cy?: number;
  marker: AlertNewsMarker;
  store: NewsMarkerStore;
  cardId: string;
}) {
  if (cx === undefined || cy === undefined) return null;
  const estimate = marker.news.estimate;
  const range = estimate?.low_eur && estimate.high_eur &&
    (estimate.status === "estimated" || estimate.status === "measured")
    ? ` ${estimate.status === "measured" ? "Impacto medido" : "Impacto estimado"} en tu cartera: ${formatEurRange(estimate.low_eur, estimate.high_eur)}${estimate.horizon_sessions ? ` a ${estimate.horizon_sessions} sesiones` : ""}.`
    : "";
  const onKeyDown = (event: KeyboardEvent<SVGGElement>) => {
    if (event.key === "Escape") store.set(null);
    if (event.key.startsWith("Arrow")) event.stopPropagation();
  };
  return (
    <g
      role="button"
      tabIndex={0}
      aria-label={`Noticia con aviso del ${pointDate(marker.marketDate)}: ${marker.news.title}.${range}`}
      aria-describedby={cardId}
      onMouseEnter={() => store.set({ marker, x: cx, y: cy })}
      onFocus={() => store.set({ marker, x: cx, y: cy })}
      onClick={() => store.set({ marker, x: cx, y: cy })}
      onKeyDown={onKeyDown}
      className="cursor-pointer"
    >
      <circle cx={cx} cy={cy} r={9} fill="var(--kairos-color-surface)" stroke="var(--kairos-color-brand-red)" strokeWidth={2.5} />
      <circle cx={cx} cy={cy} r={3} fill="var(--kairos-color-brand-red)" />
      <circle cx={cx} cy={cy} r={22} fill="transparent" />
    </g>
  );
}
