import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ApiError, apiGet } from "../client";
import type { AssetHistoryOut, HistoryPeriod } from "../generated/schema";

/**
 * Evolución de una posición (`GET /portfolios/{id}/positions/{asset_id}/history?period=`), T2-23.
 * Al cambiar de periodo se conserva la serie anterior mientras llega la nueva. Un 404 (la cartera
 * nunca tuvo el activo) no se reintenta.
 */
export function useAssetHistory(portfolioId: string, assetId: string, period: HistoryPeriod) {
  return useQuery({
    queryKey: ["asset-history", portfolioId, assetId, period],
    queryFn: ({ signal }) =>
      apiGet<AssetHistoryOut>(
        `/portfolios/${encodeURIComponent(portfolioId)}/positions/${encodeURIComponent(assetId)}/history?period=${period}`,
        { mock: "AssetHistoryOut", signal },
      ),
    placeholderData: keepPreviousData,
    retry: (count, error) => !(error instanceof ApiError && error.status === 404) && count < 2,
  });
}
