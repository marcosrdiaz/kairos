import { useMemo } from "react";
import { useEvents } from "../../../../api/hooks/useEvents";
import { useAlerts } from "../../../../api/hooks/useAlerts";
import type { ChartRow } from "../chartFormat";
import { placeMarkers, type EventMarker } from "./placeMarkers";

/**
 * Solo eventos que han generado un aviso a esta cartera. Comparte caché con el panel y
 * la bandeja. Sin avisos o datos de evento, no se dibuja ningún marcador.
 */
export function useEventMarkers(portfolioId: string, rows: ChartRow[]): EventMarker[] {
  const { data } = useEvents(portfolioId);
  const { data: alerts } = useAlerts(portfolioId);
  return useMemo(() => {
    const ids = new Set((Array.isArray(alerts) ? alerts : []).filter((a) => a.kind === "event_impact").map((a) => a.event_id));
    return placeMarkers(rows, (data ?? []).filter((event) => ids.has(event.event_id)));
  }, [rows, data, alerts]);
}
