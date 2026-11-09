import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../api/client";
import type { DcaExecutionOut, DcaPlanOut } from "../../api/generated/schema";

export const dcaPlansKey = (portfolioId: string) => ["dca-plans", portfolioId] as const;
export const pendingExecutionsKey = (portfolioId: string) =>
  ["dca-executions", portfolioId, "pending"] as const;

/** El mock es un único ejemplo; la API real devuelve una lista. */
function asList<T>(value: T | T[]): T[] {
  return Array.isArray(value) ? value : [value];
}

/** Planes de aportación de la cartera (`GET /portfolios/{id}/dca-plans`). */
export function useDcaPlans(portfolioId: string) {
  return useQuery({
    queryKey: dcaPlansKey(portfolioId),
    queryFn: async ({ signal }) =>
      asList(
        await apiGet<DcaPlanOut[] | DcaPlanOut>(
          `/portfolios/${encodeURIComponent(portfolioId)}/dca-plans`,
          { mock: "DcaPlanOut", signal },
        ),
      ),
  });
}

/** Aportaciones que esperan confirmar o saltar (`?status=pending`). */
export function usePendingExecutions(portfolioId: string) {
  return useQuery({
    queryKey: pendingExecutionsKey(portfolioId),
    queryFn: async ({ signal }) =>
      asList(
        await apiGet<DcaExecutionOut[] | DcaExecutionOut>(
          `/portfolios/${encodeURIComponent(portfolioId)}/dca-executions?status=pending`,
          { mock: "DcaExecutionOut", signal },
        ),
      ),
  });
}
