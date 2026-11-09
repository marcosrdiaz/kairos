import { useQuery } from "@tanstack/react-query";
import { apiGet, getMock } from "../../api/client";
import type { EventImpactOut } from "../../api/generated/schema";

/** Mocks con forma de EventImpactOut (cada uno es un ejemplo suelto; la ruta real devuelve una lista). */
const MOCK_NAMES = ["EventImpactOut", "EventImpactOut.nvda"];

/** Ventana de eventos del resumen de noticias. */
export const NEWS_DAYS = 30;

/**
 * Eventos que afectan a la cartera (`GET /portfolios/{id}/events`), del más reciente al más antiguo.
 * Solo los de esta cartera: si un evento no la toca, no sale (principio de personalización).
 */
export function useEventNews(portfolioId: string) {
  return useQuery({
    queryKey: ["events", portfolioId, NEWS_DAYS],
    queryFn: async ({ signal }) => {
      const list =
        import.meta.env.VITE_USE_MOCKS === "true"
          ? MOCK_NAMES.map((m) => getMock<EventImpactOut>(m)).filter(
              (e): e is EventImpactOut => e !== undefined,
            )
          : await apiGet<EventImpactOut[]>(
              `/portfolios/${encodeURIComponent(portfolioId)}/events?days=${NEWS_DAYS}`,
              { signal },
            );
      return [...list].sort((a, b) => b.occurred_at.localeCompare(a.occurred_at));
    },
  });
}
