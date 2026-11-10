import { useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import type { AlertOut } from "../../api/generated/schema";
import { alertsQuery } from "../../api/hooks/useAlerts";
import { usePortfolios } from "../portfolio-picker/usePortfolios";

export interface PortfolioRef {
  id: string;
  name: string;
}

/** Un aviso con la cartera a la que pertenece (T4-15). */
export interface PortfolioAlert {
  alert: AlertOut;
  portfolio: PortfolioRef;
}

/**
 * Carteras de la bandeja: las de `GET /portfolios` y, siempre, la elegida (aunque la lista aún
 * no haya llegado o no la traiga). Sin nombre, se usa el id.
 */
export function inboxPortfolios(
  listed: readonly { id?: string; name?: string }[] | undefined,
  currentId: string,
): PortfolioRef[] {
  const valid = (listed ?? []).filter((p): p is { id: string; name?: string } => Boolean(p.id));
  const refs = valid.map((p) => ({ id: p.id, name: p.name || p.id }));
  return refs.some((p) => p.id === currentId) ? refs : [{ id: currentId, name: currentId }, ...refs];
}

/** Del más reciente al más antiguo; a igual fecha, por id para que el orden no baile. */
export function mergeAlerts(
  portfolios: readonly PortfolioRef[],
  lists: readonly (AlertOut[] | undefined)[],
): PortfolioAlert[] {
  const merged = portfolios.flatMap((portfolio, i) =>
    (lists[i] ?? []).map((alert) => ({ alert, portfolio })),
  );
  return merged.sort(
    (a, b) =>
      b.alert.created_at.localeCompare(a.alert.created_at) || a.alert.id.localeCompare(b.alert.id),
  );
}

/**
 * Avisos de todas las carteras juntos (T4-15). Cada cartera se consulta con la misma clave que
 * `useAlerts`, cada 5 s. Las cifras y los mensajes vienen del backend; aquí solo se juntan.
 */
export function useAllAlerts(currentId: string) {
  const { data: listed } = usePortfolios();
  const portfolios = useMemo(() => inboxPortfolios(listed, currentId), [listed, currentId]);
  const results = useQueries({ queries: portfolios.map((p) => alertsQuery(p.id)) });
  return {
    portfolios,
    items: mergeAlerts(
      portfolios,
      results.map((r) => r.data),
    ), // pocas decenas de avisos: juntarlos en cada render no cuesta
    loading: results.some((r) => r.isPending),
    failed: results.some((r) => r.isError && r.data === undefined),
  };
}
