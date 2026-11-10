import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiGet, getMock } from "../client";
import type { NewsCategory, NewsItemOut } from "../generated/schema";

/** Ejemplos con forma de NewsItemOut (cada uno suelto; la ruta real devuelve una lista). */
const MOCK_NAMES = ["NewsItemOut", "NewsItemOut.pending", "NewsItemOut.not_relevant"];

/** Las noticias cambian despacio: se refrescan cada minuto, no cada 5 s como el estado. */
export const NEWS_REFRESH_MS = 60_000;

export interface NewsFilter {
  category: NewsCategory | null;
  /** `true`: solo las que afectan a la cartera (por defecto en la pantalla). */
  affecting: boolean;
}

/** Mismo filtro que el backend, para que los mocks se comporten como la ruta. */
export function filterNews(items: NewsItemOut[], filter: NewsFilter): NewsItemOut[] {
  return items.filter(
    (item) =>
      (filter.category === null || item.category === filter.category) &&
      (!filter.affecting || item.estimate?.status !== "not_relevant"),
  );
}

/** Noticias por página; «Ver más» pide otra página más (la ruta admite hasta 200). */
export const NEWS_PAGE = 30;
export const NEWS_MAX = 200;

function newsPath(portfolioId: string, filter: NewsFilter, limit: number): string {
  const params = new URLSearchParams({ affecting: String(filter.affecting), limit: String(limit) });
  if (filter.category) params.set("category", filter.category);
  return `/portfolios/${encodeURIComponent(portfolioId)}/news?${params.toString()}`;
}

/**
 * Noticias con su impacto estimado en la cartera (`GET /portfolios/{id}/news`, T4-27), de la más
 * reciente a la más antigua, como mucho `limit`. Cada cartera tiene su propia caché: las cifras
 * son de esa cartera. Al pedir más, se siguen viendo las anteriores mientras llegan.
 */
export function useNews(portfolioId: string, filter: NewsFilter, limit: number = NEWS_PAGE) {
  return useQuery({
    queryKey: ["news", portfolioId, filter.category, filter.affecting, limit],
    placeholderData: keepPreviousData,
    queryFn: async ({ signal }): Promise<NewsItemOut[]> => {
      const list =
        import.meta.env.VITE_USE_MOCKS === "true"
          ? filterNews(
              MOCK_NAMES.map((m) => getMock<NewsItemOut>(m)).filter(
                (n): n is NewsItemOut => n !== undefined,
              ),
              filter,
            )
          : await apiGet<NewsItemOut[]>(newsPath(portfolioId, filter, limit), { signal });
      return [...list].sort((a, b) => b.published_at.localeCompare(a.published_at));
    },
    refetchInterval: NEWS_REFRESH_MS,
  });
}
