import { useCallback } from "react";
import { useSearchParams } from "react-router";

/** Cartera por defecto si la URL no trae `?p=` (la del guion de demo). */
export const DEFAULT_PORTFOLIO = "laura";

/**
 * Cartera elegida, guardada en `?p=` para que sobreviva a recargas, enlaces y cambios de
 * pestaña (AppShell conserva la query). Cambiarla sustituye la entrada del historial: elegir
 * cartera no es navegar.
 */
export function usePortfolioId(): [string, (id: string) => void] {
  const [params, setParams] = useSearchParams();
  const current = params.get("p") || DEFAULT_PORTFOLIO;
  const select = useCallback(
    (id: string) =>
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set("p", id);
          return next;
        },
        { replace: true },
      ),
    [setParams],
  );
  return [current, select];
}
