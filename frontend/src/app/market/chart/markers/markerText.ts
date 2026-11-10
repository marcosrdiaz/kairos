import { formatEurRange } from "../../../../lib/format";
import { CONFIDENCE_LABEL } from "../../../news/labels";
import { pointDate } from "../chartFormat";
import type { EventMarker } from "./placeMarkers";

/** Texto que anuncia el lector de pantalla al llegar al marcador con Tab. */
export function markerLabel(marker: EventMarker): string {
  const e = marker.event;
  return `Noticia del ${pointDate(marker.marketDate)}: ${e.title}. Impacto estimado en tu cartera ${formatEurRange(
    e.low_eur,
    e.high_eur,
  )}, ${CONFIDENCE_LABEL[e.confidence].toLowerCase()}.`;
}

/** Descripción breve: la explicación aprobada si la hay; si no, la cadena causal. Sin cifras del LLM. */
export function markerSummary(marker: EventMarker): string {
  const e = marker.event;
  if (e.explanation && (e.explanation_status === "ok" || e.explanation_status === "template")) {
    return e.explanation;
  }
  return e.causal_chain.join(" → ");
}
