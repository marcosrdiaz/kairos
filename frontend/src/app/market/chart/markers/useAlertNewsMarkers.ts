import { useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import { apiGet, getMock } from "../../../../api/client";
import type { NewsItemOut } from "../../../../api/generated/schema";
import { useAlerts } from "../../../../api/hooks/useAlerts";
import type { ChartRow } from "../chartFormat";

const DAY_MS = 86_400_000;
const MAX_GAP_DAYS = 7;

export interface AlertNewsMarker {
  news: NewsItemOut;
  marketDate: string;
  date: string;
  value: number;
}

/** Solo se consultan noticias que ya han generado un aviso en esta cartera. */
export function useAlertNewsMarkers(portfolioId: string, rows: ChartRow[]): AlertNewsMarker[] {
  const { data: alerts } = useAlerts(portfolioId);
  const ids = useMemo(
    () => [...new Set((Array.isArray(alerts) ? alerts : []).filter((a) => a.kind === "news_estimate" && a.news_id).map((a) => a.news_id!))],
    [alerts],
  );
  const results = useQueries({
    queries: ids.map((id) => ({
      queryKey: ["news", portfolioId, id],
      queryFn: async ({ signal }: { signal: AbortSignal }): Promise<NewsItemOut | null> => {
        if (import.meta.env.VITE_USE_MOCKS === "true") {
          const mock = getMock<NewsItemOut>("NewsItemOut");
          return mock?.id === id ? mock : null;
        }
        return apiGet<NewsItemOut>(`/portfolios/${encodeURIComponent(portfolioId)}/news/${encodeURIComponent(id)}`, { signal });
      },
      staleTime: 60_000,
    })),
  });
  const news = results.map((r) => r.data).filter((n): n is NewsItemOut => Boolean(n));
  if (rows.length === 0) return [];
  const days = rows.map((r) => Math.floor(Date.parse(r.date) / DAY_MS));
  return news.flatMap((item) => {
    const target = Math.floor(Date.parse(item.published_at) / DAY_MS);
    let best = -1;
    let gap = Infinity;
    days.forEach((day, index) => {
      const distance = Math.abs(day - target);
      if (distance < gap) { gap = distance; best = index; }
    });
    const row = rows[best];
    return row && gap <= MAX_GAP_DAYS
      ? [{ news: item, marketDate: item.published_at, date: row.date, value: row.value }]
      : [];
  });
}
