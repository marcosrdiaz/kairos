import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiPost } from "../client";
import type { AssetCreateRequest, AssetOut } from "../generated/schema";

/** Prefijo de las claves de `useAssetLookup` (`["assets", "lookup", q]`). */
const LOOKUP_KEY = ["assets", "lookup"] as const;

/**
 * `POST /assets` (T4-07): busca el activo en el mercado por ISIN, ticker o nombre y lo da de
 * alta en el catálogo. Si ya estaba, devuelve ese. 404 si el mercado no lo conoce; 503 si no
 * responde o la app está en modo demo (en ambos, `ApiError.serverMessage` lo explica).
 */
export function useCreateAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (query: string) => {
      const body: AssetCreateRequest = { query };
      return apiPost<AssetOut>("/assets", body, { mock: "AssetOut" });
    },
    onSuccess: () => {
      // El activo nuevo ya sale en el buscador local.
      void queryClient.invalidateQueries({ queryKey: LOOKUP_KEY });
    },
  });
}
