import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { HistoryPeriod, PortfolioHistoryOut } from "../generated/schema";

/**
 * Evolución del valor de la cartera (`GET /portfolios/{id}/history?period=`), T2-18.
 * Al cambiar de periodo se conserva la serie anterior mientras llega la nueva (sin saltos).
 */
export function usePortfolioHistory(portfolioId: string, period: HistoryPeriod) {
  return useQuery({
    queryKey: ["history", portfolioId, period],
    queryFn: ({ signal }) =>
      apiGet<PortfolioHistoryOut>(
        `/portfolios/${encodeURIComponent(portfolioId)}/history?period=${period}`,
        { mock: "PortfolioHistoryOut", signal },
      ),
    placeholderData: keepPreviousData,
  });
}
