import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import type { StatusOut } from "../api/generated/schema";

/** Lectura única del estado precalculado. El polling cada 5 s es de T2-13. */
export function useStatus(portfolioId: string) {
  return useQuery({
    queryKey: ["status", portfolioId],
    queryFn: ({ signal }) =>
      apiGet<StatusOut>(`/portfolios/${encodeURIComponent(portfolioId)}/status`, {
        mock: "StatusOut",
        signal,
      }),
  });
}
