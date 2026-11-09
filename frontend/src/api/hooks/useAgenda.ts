import { useQuery } from "@tanstack/react-query";
import { apiGet, getMock } from "../client";
import type { AgendaItemOut } from "../generated/schema";

/** Mocks con forma de AgendaItemOut (cada uno es un ejemplo suelto; la ruta real devuelve una lista). */
const MOCK_NAMES = ["AgendaItemOut", "AgendaItemOut.dca"];

/**
 * Próximos eventos y aportaciones, con lo que tienes expuesto a cada uno
 * (`GET /portfolios/{id}/agenda`). Hasta T2-06 el backend responde con el ejemplo fijo del
 * contrato; el panel lo muestra tal cual. Del más próximo al más lejano.
 */
export function useAgenda(portfolioId: string) {
  return useQuery({
    queryKey: ["agenda", portfolioId],
    queryFn: async ({ signal }): Promise<AgendaItemOut[]> => {
      const list =
        import.meta.env.VITE_USE_MOCKS === "true"
          ? MOCK_NAMES.map((m) => getMock<AgendaItemOut>(m)).filter(
              (e): e is AgendaItemOut => e !== undefined,
            )
          : await apiGet<AgendaItemOut[]>(`/portfolios/${encodeURIComponent(portfolioId)}/agenda`, {
              signal,
            });
      return [...list].sort((a, b) => a.date.localeCompare(b.date));
    },
  });
}
