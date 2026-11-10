import { useEffect } from "react";
import { useSearchParams } from "react-router";
import { usePortfolioId } from "./usePortfolioId";
import { usePortfolios } from "./usePortfolios";
import { readStoredPortfolio, writeStoredPortfolio } from "./storedPortfolio";

/**
 * Mantiene `?p=` apuntando a una cartera que existe (T4-13). Lo usa el selector, que está
 * montado en toda la app (barra lateral y cabecera del panel):
 * - `?p=` válido: se recuerda en el navegador.
 * - Sin `?p=`, o con una cartera que ya no está (borrada, enlace viejo): la última elegida si
 *   sigue existiendo y, si no, la primera de la lista.
 * - Lista vacía: no hace nada; `FirstRunGate` abre el asistente.
 */
export function useSyncPortfolioId(): void {
  const [params] = useSearchParams();
  const [, select] = usePortfolioId();
  const { data } = usePortfolios();
  const fromUrl = params.get("p");

  useEffect(() => {
    if (!data || data.length === 0) return;
    const ids = data.map((p) => p.id);
    if (fromUrl && ids.includes(fromUrl)) {
      writeStoredPortfolio(fromUrl);
      return;
    }
    const stored = readStoredPortfolio();
    const next = stored && ids.includes(stored) ? stored : ids[0];
    if (next && next !== fromUrl) select(next);
  }, [data, fromUrl, select]);
}
