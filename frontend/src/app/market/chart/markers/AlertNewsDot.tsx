import type { KeyboardEvent } from "react";
import { formatEurRange } from "../../../../lib/format";
import { pointDate } from "../chartFormat";
import { NEWS_CATEGORY_ICON_PATH } from "./newsCategoryIconPaths";
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
      <circle cx={cx} cy={cy} r={21} fill="var(--kairos-color-primary)" opacity={0.24} />
      <circle cx={cx} cy={cy} r={16} fill="var(--kairos-color-primary)" stroke="var(--kairos-color-surface)" strokeWidth={2.5} />
      <path
        d={NEWS_CATEGORY_ICON_PATH[marker.news.category]}
        transform={`translate(${cx - 6} ${cy - 6})`}
        fill="none"
        stroke="var(--kairos-color-on-primary)"
        strokeWidth={1.2}
        strokeLinecap="round"
        strokeLinejoin="round"
        pointerEvents="none"
      />
      <circle cx={cx} cy={cy} r={22} fill="transparent" />
    </g>
  );
}
