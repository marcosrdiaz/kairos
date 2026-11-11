import { useQuery } from "@tanstack/react-query";
import { ApiError, apiGet } from "../client";
import type { PlanOut } from "../generated/schema";

/**
 * Plan de inversión de la cartera (`GET /portfolios/{id}/plan`): reparto objetivo, umbral,
 * reparto actual y desviación, ya calculados por el backend. Una cartera nueva puede no tener
 * plan (404): no se reintenta y la pantalla lo dice.
 */
export function usePlan(portfolioId: string) {
  return useQuery({
    queryKey: ["plan", portfolioId],
    queryFn: ({ signal }) =>
      apiGet<PlanOut>(`/portfolios/${encodeURIComponent(portfolioId)}/plan`, {
        mock: "PlanOut",
        signal,
      }),
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 2,
  });
}

/** `true` si el error es «esta cartera aún no tiene plan» y no un fallo del servicio. */
export function isPlanMissing(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}
