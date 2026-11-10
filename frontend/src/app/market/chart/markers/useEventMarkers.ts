import { useMemo } from "react";
import { useEvents } from "../../../../api/hooks/useEvents";
import type { ChartRow } from "../chartFormat";
import { placeMarkers, type EventMarker } from "./placeMarkers";

/**
 * Noticias de la cartera colocadas sobre la serie (T2-22). Usa la misma consulta que el panel y
 * el carrusel de Inicio (`useEvents`, misma caché), así que no hace peticiones de más. Mientras
 * carga o si falla, no hay marcadores: la gráfica se ve igual, sin inventar nada.
 */
export function useEventMarkers(portfolioId: string, rows: ChartRow[]): EventMarker[] {
  const { data } = useEvents(portfolioId);
  return useMemo(() => placeMarkers(rows, data ?? []), [rows, data]);
}
