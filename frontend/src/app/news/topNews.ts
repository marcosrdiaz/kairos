import type { NewsItemOut } from "../../api/generated/schema";

/** Cuántas noticias enseña Inicio. */
export const TOP_NEWS = 5;

/** Ventana de Inicio: lo que se ha publicado en las últimas 24 horas. */
export const TOP_NEWS_WINDOW_MS = 24 * 60 * 60 * 1000;

/** Las que tienen cifra (estimada o medida) para esta cartera. */
function hasFigure(item: NewsItemOut): boolean {
  const status = item.estimate?.status;
  return (status === "estimated" || status === "measured") && !!item.estimate?.impact_eur;
}

/** Tamaño del impacto que llega del backend, solo para ordenar (no se pinta ni se opera). */
function magnitude(item: NewsItemOut): number {
  return Math.abs(Number(item.estimate?.impact_eur ?? 0));
}

/**
 * Las noticias más relevantes para la cartera en las últimas 24 horas: publicadas entre
 * `now - 24 h` y `now` (reloj del backend), con impacto estimado o medido, ordenadas por el tamaño
 * de `impact_eur` (de mayor a menor; a igualdad, la más reciente) y como mucho `TOP_NEWS`.
 * Ordenar no es calcular: las cifras llegan tal cual del motor de impacto.
 */
export function topNews(items: NewsItemOut[], now: Date, max: number = TOP_NEWS): NewsItemOut[] {
  const end = now.getTime();
  const start = end - TOP_NEWS_WINDOW_MS;
  return items
    .filter((item) => {
      const published = Date.parse(item.published_at);
      return published >= start && published <= end && hasFigure(item);
    })
    .sort(
      (a, b) => magnitude(b) - magnitude(a) || b.published_at.localeCompare(a.published_at),
    )
    .slice(0, max);
}
