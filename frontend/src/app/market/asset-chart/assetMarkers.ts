import type { EventImpactOut } from "../../../api/generated/schema";
import type { ChartRow } from "../chart/chartFormat";
import { placeMarkers, type EventMarker } from "../chart/markers/placeMarkers";

const isZero = (v: string) => /^[+-]?0*(\.0*)?$/.test(v.trim());

/**
 * Noticias que afectan a una posición (T2-23), colocadas sobre su serie: las que tienen a ese
 * activo en `breakdown` con impacto distinto de cero y con rango. Cada marcador lleva el impacto
 * en la posición (`position`), no el de la cartera. Los impactos guardados antes del rango por
 * posición no se dibujan: nunca una cifra sin rango. Puro: sin red ni React.
 */
export function placeAssetMarkers(rows: ChartRow[], events: EventImpactOut[], assetId: string): EventMarker[] {
  const positions = new Map<string, NonNullable<EventMarker["position"]>>();
  for (const event of events) {
    const hit = event.breakdown.find((b) => b.asset_id === assetId);
    if (!hit?.low_eur || !hit.high_eur || isZero(hit.impact_eur)) continue;
    positions.set(event.event_id, { name: hit.name, low_eur: hit.low_eur, high_eur: hit.high_eur });
  }
  const affecting = events.filter((e) => positions.has(e.event_id));
  return placeMarkers(rows, affecting).map((m) => ({ ...m, position: positions.get(m.event.event_id) }));
}
