import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { TickerOut } from "../generated/schema";

/** Los precios son cierres diarios: basta con refrescar cada minuto (y al volver a la pestaña). */
const TICKER_REFRESH_MS = 60_000;

/**
 * Ticker de mercado de Inicio (`GET /portfolios/{id}/ticker`, T2-17): último precio de cada
 * posición y su variación frente al cierre anterior, calculada en el backend con `calc_id`.
 */
export function useTicker(portfolioId: string) {
  return useQuery({
    queryKey: ["ticker", portfolioId],
    queryFn: ({ signal }) =>
      apiGet<TickerOut>(`/portfolios/${encodeURIComponent(portfolioId)}/ticker`, {
        mock: "TickerOut",
        signal,
      }),
    refetchInterval: TICKER_REFRESH_MS,
  });
}
