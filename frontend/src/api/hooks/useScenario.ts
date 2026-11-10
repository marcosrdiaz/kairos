import { useQuery } from "@tanstack/react-query";
import { apiPost } from "../client";
import type { ScenarioOut } from "../generated/schema";

/** Variación de cada factor como fracción en texto decimal (`"-0.10"` = −10 %). */
export type FactorShocks = Partial<Record<"EQ_GLOBAL" | "EQ_US_TECH" | "RATES_EUR" | "OIL" | "EURUSD", string>>;

/**
 * Escenario ¿Y si…? (`POST /portfolios/{id}/scenarios`, RF-21). No cambia nada en la cartera:
 * solo calcula, así que se cachea por cartera y escenario. Sin escenario elegido no se llama.
 */
export function useScenario(portfolioId: string, scenarioId: string | null, shocks: FactorShocks | null) {
  return useQuery({
    queryKey: ["scenario", portfolioId, scenarioId],
    queryFn: ({ signal }) =>
      apiPost<ScenarioOut>(
        `/portfolios/${encodeURIComponent(portfolioId)}/scenarios`,
        { factor_shocks: shocks },
        { mock: "ScenarioOut", signal },
      ),
    enabled: scenarioId !== null && shocks !== null,
    staleTime: 60_000,
  });
}
