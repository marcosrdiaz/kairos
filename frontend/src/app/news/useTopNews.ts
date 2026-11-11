import { useQuery } from "@tanstack/react-query";
import { apiGet, getMock } from "../../api/client";
import type { NewsItemOut } from "../../api/generated/schema";
import { NEWS_MAX, NEWS_REFRESH_MS } from "../../api/hooks/useNews";
import { topNews } from "./topNews";

/** Ejemplos con forma de NewsItemOut (cada uno suelto; la ruta real devuelve una lista). */
const MOCK_NAMES = ["NewsItemOut", "NewsItemOut.pending", "NewsItemOut.not_relevant"];

/** Lo que usa Inicio de `GET /health`: la hora del backend (fija en modo demo, D-080). */
interface HealthClock {
  now: string;
}

/**
 * Las 5 noticias con más impacto en la cartera en las últimas 24 horas (TD-04).
 *
 * Pide las noticias que afectan a la cartera (`GET /portfolios/{id}/news?affecting=true`, de la
 * más reciente a la más antigua, hasta el reloj del backend) y la hora del backend
 * (`GET /health`), para que «24 horas» signifique lo mismo en producción y con el reloj fijo de
 * la demo. Con mocks no hay reloj: la ventana termina en la noticia más reciente.
 */
export function useTopNews(portfolioId: string) {
  return useQuery({
    queryKey: ["news", "top", portfolioId],
    queryFn: async ({ signal }): Promise<NewsItemOut[]> => {
      if (import.meta.env.VITE_USE_MOCKS === "true") {
        const items = MOCK_NAMES.map((m) => getMock<NewsItemOut>(m)).filter(
          (n): n is NewsItemOut => n !== undefined,
        );
        const newest = items.map((n) => n.published_at).sort().at(-1);
        return newest ? topNews(items, new Date(newest)) : [];
      }
      const path = `/portfolios/${encodeURIComponent(portfolioId)}/news?affecting=true&limit=${NEWS_MAX}`;
      const [items, health] = await Promise.all([
        apiGet<NewsItemOut[]>(path, { signal }),
        apiGet<HealthClock>("/health", { signal }),
      ]);
      return topNews(items, new Date(health.now));
    },
    refetchInterval: NEWS_REFRESH_MS,
  });
}
