import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { StatusOut } from "../generated/schema";
import { POLL_INTERVAL_MS } from "./polling";

/** Estado precalculado de la cartera, consultado cada 5 s mientras la pantalla está abierta. */
export function useStatus(portfolioId: string) {
  return useQuery({
    queryKey: ["status", portfolioId],
    queryFn: ({ signal }) =>
      apiGet<StatusOut>(`/portfolios/${encodeURIComponent(portfolioId)}/status`, {
        mock: "StatusOut",
        signal,
      }),
    refetchInterval: POLL_INTERVAL_MS,
  });
}
