import { formatEurRange } from "../../../../lib/format";
import { CONFIDENCE_LABEL } from "../../../news/labels";
import { pointDate } from "../chartFormat";
import type { EventMarker } from "./placeMarkers";

/** A qué se refiere el impacto del marcador y su rango: la cartera o, en la gráfica de una
 *  posición (T2-23), esa posición. Cifras del backend. */
export function markerImpact(marker: EventMarker): { scope: string; range: string } {
  const p = marker.position;
  if (p) return { scope: `en ${p.name}`, range: formatEurRange(p.low_eur, p.high_eur) };
  const e = marker.event;
  return { scope: "en tu cartera", range: formatEurRange(e.low_eur, e.high_eur) };
}

/** Texto que anuncia el lector de pantalla al llegar al marcador con Tab. */
export function markerLabel(marker: EventMarker): string {
  const e = marker.event;
  const { scope, range } = markerImpact(marker);
  return `Noticia del ${pointDate(marker.marketDate)}: ${e.title}. Impacto estimado ${scope} ${range}, ${CONFIDENCE_LABEL[
    e.confidence
  ].toLowerCase()}.`;
}

/** Descripción breve: la explicación aprobada si la hay; si no, la cadena causal. Sin cifras del LLM. */
export function markerSummary(marker: EventMarker): string {
  const e = marker.event;
  if (e.explanation && (e.explanation_status === "ok" || e.explanation_status === "template")) {
    return e.explanation;
  }
  return e.causal_chain.join(" → ");
}
