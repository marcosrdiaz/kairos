import type { KeyboardEvent } from "react";
import type { EventType } from "../../../news/labels";
import type { MarkerStore } from "./markerStore";
import { markerLabel } from "./markerText";
import type { EventMarker } from "./placeMarkers";

/** Glifo de 12 × 12 por tipo de evento (decorativo: el tipo va en el texto). */
const GLYPH: Record<EventType, string> = {
  central_bank: "M1 4.5 6 1.5l5 3M2 5v4.5M4.67 5v4.5M7.33 5v4.5M10 5v4.5M1 10.5h10",
  commodity: "M6 1C6 1 2.5 5 2.5 7.5a3.5 3.5 0 0 0 7 0C9.5 5 6 1 6 1Z",
  earnings: "M1.5 10.5h9M3 10V6.5M6 10V3.5M9 10V5",
  fx: "M2 4h7l-2-2M10 8H3l2 2",
  macro: "M6 1a5 5 0 1 0 0 10A5 5 0 0 0 6 1Zm-5 5h10M6 1c1.5 1.4 2 3 2 5s-.5 3.6-2 5c-1.5-1.4-2-3-2-5s.5-3.6 2-5Z",
};

/** El círculo va por encima del punto, unido a la línea por un trazo; cada piso sube 30 px. */
const LIFT = 26;
const LEVEL_PX = 30;

interface EventMarkerDotProps {
  cx?: number;
  cy?: number;
  marker: EventMarker;
  /** Piso (0, 1…): las noticias cercanas se apilan para no pisarse. */
  level?: number;
  store: MarkerStore;
  /** Id de la tarjeta, para `aria-describedby`. */
  cardId: string;
}

/**
 * Marcador de una noticia en la gráfica (forma de `ReferenceDot`): un círculo con el glifo del tipo
 * de evento, unido al punto de la línea. Se enfoca con Tab (`role="button"` con nombre completo);
 * con el ratón o el foco abre la tarjeta (por el almacén, sin repintar la gráfica) y Escape la
 * cierra. Las flechas no se propagan a la gráfica, que las usa para recorrer los días.
 */
export function EventMarkerDot({ cx, cy, marker, level = 0, store, cardId }: EventMarkerDotProps) {
  if (cx === undefined || cy === undefined) return null;
  const top = cy - LIFT - level * LEVEL_PX;
  const show = () => store.set({ marker, x: cx, y: top });
  const hide = () => store.set(null);
  const onKeyDown = (e: KeyboardEvent<SVGGElement>) => {
    if (e.key === "Escape") hide();
    if (e.key.startsWith("Arrow")) e.stopPropagation();
  };
  return (
    <g
      className="kchart-marker"
      tabIndex={0}
      role="button"
      aria-label={markerLabel(marker)}
      aria-describedby={cardId}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      onKeyDown={onKeyDown}
    >
      <line x1={cx} x2={cx} y1={top + 12} y2={cy - 3} stroke="var(--kairos-color-primary)" strokeWidth={1.5} />
      <circle cx={cx} cy={cy} r={3.5} fill="var(--kairos-color-primary)" />
      <circle className="kchart-marker-halo" cx={cx} cy={top} r={17} fill="var(--kairos-color-primary)" />
      <circle cx={cx} cy={top} r={12} fill="var(--kairos-color-surface)" stroke="var(--kairos-color-primary)" strokeWidth={2} />
      <path
        d={GLYPH[marker.event.event_type]}
        transform={`translate(${cx - 6} ${top - 6})`}
        fill="none"
        stroke="var(--kairos-color-primary)"
        strokeWidth={1.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Objetivo de 44 px para el ratón y el tacto, sin pintar. */}
      <circle cx={cx} cy={top} r={22} fill="transparent" />
    </g>
  );
}
