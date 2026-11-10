import { useQuery } from "@tanstack/react-query";
import { apiGet, getMock } from "../client";
import type { AlertOut } from "../generated/schema";
import { POLL_INTERVAL_MS } from "./polling";

/**
 * Consulta de los avisos de una cartera. La comparten `useAlerts` y la bandeja de todas las
 * carteras (`app/alerts/useAllAlerts`), así que leen la misma caché.
 */
export function alertsQuery(portfolioId: string) {
  return {
    queryKey: ["alerts", portfolioId],
    queryFn: async ({ signal }: { signal: AbortSignal }): Promise<AlertOut[]> => {
      if (import.meta.env.VITE_USE_MOCKS === "true") {
        const example = getMock<AlertOut>("AlertOut"); // el ejemplo es uno suelto; la ruta da lista
        return example ? [example] : [];
      }
      return apiGet<AlertOut[]>(`/portfolios/${encodeURIComponent(portfolioId)}/alerts`, { signal });
    },
    refetchInterval: POLL_INTERVAL_MS,
  };
}

/** Avisos de la cartera, del más reciente al más antiguo, consultados cada 5 s. */
export function useAlerts(portfolioId: string) {
  return useQuery(alertsQuery(portfolioId));
}
