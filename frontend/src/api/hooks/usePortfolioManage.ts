import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiPatch } from "../client";
import type { PortfolioSummaryOut, PortfolioUpdateRequest } from "../generated/schema";

/** Misma clave que `usePortfolios` (lista del selector). */
const PORTFOLIOS_KEY = ["portfolios"] as const;

/** `PATCH /portfolios/{id}`: renombra (o cambia tipo o perfil). Actualiza la lista sin recargarla. */
export function useUpdatePortfolio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: PortfolioUpdateRequest }) =>
      apiPatch<PortfolioSummaryOut>(`/portfolios/${encodeURIComponent(id)}`, body, {
        mock: "PortfolioSummaryOut",
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData<PortfolioSummaryOut[]>(PORTFOLIOS_KEY, (list) =>
        (list ?? []).map((p) => (p.id === updated.id ? updated : p)),
      );
    },
  });
}

/**
 * `DELETE /portfolios/{id}`: el backend borra la cartera con todo lo suyo. Se quita de la lista
 * en el acto (si era la última, `FirstRunGate` reabre el asistente) y se olvidan sus datos.
 */
export function useDeletePortfolio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/portfolios/${encodeURIComponent(id)}`),
    onSuccess: (_out, id) => {
      queryClient.setQueryData<PortfolioSummaryOut[]>(PORTFOLIOS_KEY, (list) =>
        (list ?? []).filter((p) => p.id !== id),
      );
      // Las claves por cartera llevan su id en la segunda posición (["status", id], …).
      queryClient.removeQueries({ predicate: (q) => q.queryKey[1] === id });
    },
  });
}
