import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { PortfolioOut } from "../generated/schema";
import { POLL_INTERVAL_MS } from "./polling";

/**
 * Cartera valorada (`GET /portfolios/{id}`) con consulta cada 5 s: tras un replay, el ajuste de
 * demo cambia la valoración y el panel debe reflejarlo sin recargar. Misma clave que
 * `usePortfolio` de Cartera, así que las dos pantallas comparten caché.
 */
export function useLivePortfolio(portfolioId: string) {
  return useQuery({
    queryKey: ["portfolio", portfolioId],
    queryFn: ({ signal }) =>
      apiGet<PortfolioOut>(`/portfolios/${encodeURIComponent(portfolioId)}`, {
        mock: "PortfolioOut",
        signal,
      }),
    refetchInterval: POLL_INTERVAL_MS,
  });
}
