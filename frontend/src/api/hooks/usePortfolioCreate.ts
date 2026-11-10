import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiPost } from "../client";
import type {
  PortfolioCreateRequest,
  PortfolioImportOut,
  PortfolioImportRequest,
  PortfolioSummaryOut,
} from "../generated/schema";

/** Misma clave que `usePortfolios` (lista del selector). */
const PORTFOLIOS_KEY = ["portfolios"] as const;

/**
 * Añade la cartera nueva a la lista ya cargada sin esperar a otra petición, para que quien
 * dependa de que haya carteras (el asistente de primer uso) lo vea en el mismo render.
 */
function appendPortfolio(list: PortfolioSummaryOut[] | undefined, p: PortfolioSummaryOut) {
  const rest = (list ?? []).filter((x) => x.id !== p.id);
  return [...rest, p];
}

/** `POST /portfolios`: crea una cartera vacía (las posiciones se dan de alta después). */
export function useCreatePortfolio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: PortfolioCreateRequest) =>
      apiPost<PortfolioSummaryOut>("/portfolios", body, { mock: "PortfolioSummaryOut" }),
    onSuccess: (created) => {
      queryClient.setQueryData<PortfolioSummaryOut[]>(PORTFOLIOS_KEY, (list) =>
        appendPortfolio(list, created),
      );
    },
  });
}

/**
 * `POST /portfolios/import`: crea una cartera desde el texto de un CSV. Si alguna fila falla,
 * el backend no crea nada y responde 422 con `details.rows`.
 */
export function useImportPortfolio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: PortfolioImportRequest) =>
      apiPost<PortfolioImportOut>("/portfolios/import", body, { mock: "PortfolioImportOut" }),
    onSuccess: (out) => {
      const created = out.portfolio;
      if (!created) return;
      queryClient.setQueryData<PortfolioSummaryOut[]>(PORTFOLIOS_KEY, (list) =>
        appendPortfolio(list, created),
      );
      void queryClient.invalidateQueries();
    },
  });
}
