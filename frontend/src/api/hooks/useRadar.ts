import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { RadarOut } from "../generated/schema";
import { POLL_INTERVAL_MS } from "./polling";

/**
 * Radar de riesgos y oportunidades (`GET /portfolios/{id}/radar`). Se consulta cada 5 s: una
 * operación, una aportación o un replay pueden cambiar lo que sale.
 */
export function useRadar(portfolioId: string) {
  return useQuery({
    queryKey: ["radar", portfolioId],
    queryFn: ({ signal }) =>
      apiGet<RadarOut>(`/portfolios/${encodeURIComponent(portfolioId)}/radar`, {
        mock: "RadarOut",
        signal,
      }),
    refetchInterval: POLL_INTERVAL_MS,
  });
}
