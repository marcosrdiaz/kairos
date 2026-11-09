import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../api/client";
import type { PortfolioSummaryOut } from "../../api/generated/schema";

export const PORTFOLIOS_KEY = ["portfolios"] as const;

/** El mock es un único ejemplo; la API real devuelve una lista. */
function asList<T>(value: T | T[]): T[] {
  return Array.isArray(value) ? value : [value];
}

/** Carteras disponibles (`GET /portfolios`): hoy, Laura y Javier. */
export function usePortfolios() {
  return useQuery({
    queryKey: PORTFOLIOS_KEY,
    queryFn: async ({ signal }) =>
      asList(
        await apiGet<PortfolioSummaryOut[] | PortfolioSummaryOut>("/portfolios", {
          mock: "PortfolioSummaryOut",
          signal,
        }),
      ),
    staleTime: 60_000,
  });
}
