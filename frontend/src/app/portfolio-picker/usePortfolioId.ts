import { useCallback } from "react";
import { useSearchParams } from "react-router";
import { readStoredPortfolio, writeStoredPortfolio } from "./storedPortfolio";

/** Cartera por defecto si no hay `?p=` ni una guardada (la del guion de demo). */
export const DEFAULT_PORTFOLIO = "laura";

/**
 * Cartera elegida, guardada en `?p=` para que sobreviva a recargas, enlaces y cambios de
 * pestaña (AppShell conserva la query), y en el navegador para la próxima visita (T4-13).
 * Sin `?p=`, la última elegida; `useSyncPortfolioId` la escribe en la URL en cuanto se sabe
 * qué carteras hay. Cambiarla sustituye la entrada del historial: elegir cartera no es navegar.
 */
export function usePortfolioId(): [string, (id: string) => void] {
  const [params, setParams] = useSearchParams();
  const current = params.get("p") || readStoredPortfolio() || DEFAULT_PORTFOLIO;
  const select = useCallback(
    (id: string) => {
      writeStoredPortfolio(id);
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set("p", id);
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );
  return [current, select];
}
