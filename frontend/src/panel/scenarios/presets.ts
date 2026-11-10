import type { FactorShocks } from "../../api/hooks/useScenario";

/**
 * Escenarios ¿Y si…? que el usuario puede probar (UC-09). Son supuestos que elige él, no
 * previsiones: el impacto lo calcula el motor con las betas de cada activo. Las variaciones van
 * como fracción; `RATES_EUR` es la variación de la rentabilidad del bono (0.01 = 1 punto).
 */
export interface ScenarioPreset {
  id: string;
  label: string;
  /** Qué se supone, en una frase. */
  description: string;
  shocks: FactorShocks;
}

export const SCENARIO_PRESETS: readonly ScenarioPreset[] = [
  {
    id: "bolsa-10",
    label: "La bolsa mundial cae un 10 %",
    description: "Supone una caída del 10 % de la bolsa mundial y nada más.",
    shocks: { EQ_GLOBAL: "-0.10" },
  },
  {
    id: "tecnologicas-15",
    label: "Las tecnológicas de EE. UU. caen un 15 %",
    description: "Supone una caída del 15 % de las tecnológicas estadounidenses.",
    shocks: { EQ_US_TECH: "-0.15" },
  },
  {
    id: "euro-5",
    label: "El euro sube un 5 % frente al dólar",
    description: "Supone que el euro se aprecia un 5 %: lo que cotiza en dólares vale menos en euros.",
    shocks: { EURUSD: "0.05" },
  },
  {
    id: "tipos-1",
    label: "Los tipos del euro suben 1 punto",
    description: "Supone que la rentabilidad del bono en euros sube 1 punto porcentual.",
    shocks: { RATES_EUR: "0.01" },
  },
  {
    id: "petroleo-20",
    label: "El petróleo sube un 20 %",
    description: "Supone una subida del 20 % del precio del crudo.",
    shocks: { OIL: "0.20" },
  },
];
