import { useQuery } from "@tanstack/react-query";
import { apiGet, getMock } from "../client";
import type { EventImpactOut } from "../generated/schema";
import { POLL_INTERVAL_MS } from "./polling";

/** Mocks con forma de EventImpactOut (cada uno es un ejemplo suelto; la ruta real devuelve una lista). */
const MOCK_NAMES = ["EventImpactOut", "EventImpactOut.nvda"];

/** Ventana de eventos del panel, la misma que el resumen de noticias de Inicio (comparten caché). */
export const EVENTS_DAYS = 30;

/**
 * Eventos que afectan a la cartera (`GET /portfolios/{id}/events`), del más reciente al más
 * antiguo. Se consulta cada 5 s para que el panel recoja un replay sin recargar. La clave
 * coincide con la del carrusel de Inicio, así que los dos leen la misma caché.
 */
export function useEvents(portfolioId: string) {
  return useQuery({
    queryKey: ["events", portfolioId, EVENTS_DAYS],
    queryFn: async ({ signal }): Promise<EventImpactOut[]> => {
      const list =
        import.meta.env.VITE_USE_MOCKS === "true"
          ? MOCK_NAMES.map((m) => getMock<EventImpactOut>(m)).filter(
              (e): e is EventImpactOut => e !== undefined,
            )
          : await apiGet<EventImpactOut[]>(
              `/portfolios/${encodeURIComponent(portfolioId)}/events?days=${EVENTS_DAYS}`,
              { signal },
            );
      return [...list].sort((a, b) => b.occurred_at.localeCompare(a.occurred_at));
    },
    refetchInterval: POLL_INTERVAL_MS,
  });
}
