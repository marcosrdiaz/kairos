import { ApiError } from "../../api/client";
import type { AssetOut } from "../../api/generated/schema";
import { useCreateAsset } from "../../api/hooks/useCreateAsset";

const FALLBACK = "No hemos podido buscar en el mercado ahora mismo. Vuelve a intentarlo.";

/** Texto del fallo: el `message` del backend (404 y 503 ya lo explican) o uno genérico. */
export function marketErrorText(error: unknown): string {
  return error instanceof ApiError && error.serverMessage ? error.serverMessage : FALLBACK;
}

/**
 * Opción «Buscar en el mercado» del buscador de activos (T4-07): da de alta el activo con
 * `POST /assets` y, si va bien, se lo pasa a `onFound`. `statusText` es lo que se anuncia en la
 * región `status` (búsqueda en curso o el error).
 */
export function useMarketSearch(onFound: (asset: AssetOut) => void) {
  const create = useCreateAsset();

  function search(query: string) {
    if (create.isPending) return;
    create.mutate(query, { onSuccess: onFound });
  }

  let statusText = "";
  if (create.isPending) statusText = `Buscando «${create.variables}» en el mercado…`;
  else if (create.isError) statusText = marketErrorText(create.error);

  return { search, pending: create.isPending, statusText, reset: create.reset };
}
