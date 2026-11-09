import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { ExposureOut } from "../generated/schema";

/**
 * Exposición con look-through (`GET /portfolios/{id}/exposure`): país, sector, divisa, mayores
 * empresas y solapamientos. Cambia solo cuando cambian las posiciones, así que no se consulta
 * en bucle; las operaciones de Cartera invalidan la clave `["exposure", id]` si hace falta.
 */
export function useExposure(portfolioId: string) {
  return useQuery({
    queryKey: ["exposure", portfolioId],
    queryFn: ({ signal }) =>
      apiGet<ExposureOut>(`/portfolios/${encodeURIComponent(portfolioId)}/exposure`, {
        mock: "ExposureOut",
        signal,
      }),
  });
}
