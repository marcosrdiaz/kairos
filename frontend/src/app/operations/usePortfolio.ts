import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../api/client";
import type { PortfolioOut, PositionOut } from "../../api/generated/schema";

export const portfolioKey = (portfolioId: string) => ["portfolio", portfolioId] as const;

/**
 * Cartera valorada (`GET /portfolios/{id}`): de aquí salen las posiciones que se pueden
 * vender o traspasar y los nombres de los activos de los planes de aportación.
 */
export function usePortfolio(portfolioId: string) {
  return useQuery({
    queryKey: portfolioKey(portfolioId),
    queryFn: ({ signal }) =>
      apiGet<PortfolioOut>(`/portfolios/${encodeURIComponent(portfolioId)}`, {
        mock: "PortfolioOut",
        signal,
      }),
  });
}

/** Posición por `asset_id`, o undefined si la cartera aún no ha cargado o no la tiene. */
export function findPosition(
  portfolio: PortfolioOut | undefined,
  assetId: string,
): PositionOut | undefined {
  return portfolio?.positions.find((p) => p.asset_id === assetId);
}

/** Nombre del activo si está en la cartera; si no, su identificador (sin inventar nada). */
export function assetName(portfolio: PortfolioOut | undefined, assetId: string): string {
  return findPosition(portfolio, assetId)?.name ?? assetId;
}

const priceFormatters = new Map<string, Intl.NumberFormat>();

/**
 * Precio unitario en la divisa del activo ("228.10000000", "USD" -> "228,10 US$"). Como
 * `formatEur`, no pasa por `number`: Intl acepta el string decimal tal cual. Sin divisa
 * conocida, solo la cifra.
 */
export function formatPrice(value: string, currency?: string): string {
  const key = currency ?? "";
  let f = priceFormatters.get(key);
  if (!f) {
    f = new Intl.NumberFormat("es-ES", {
      ...(currency ? { style: "currency", currency } : {}),
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
      roundingMode: "halfEven",
    });
    priceFormatters.set(key, f);
  }
  return f.format(value as `${number}`);
}
