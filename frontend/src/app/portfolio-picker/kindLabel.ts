import type { PortfolioSummaryOut } from "../../api/generated/schema";
import { KIND_OPTIONS } from "../onboarding/portfolioDetails";

/** «Personal», «Negocio», «Familia» u «Otra»; "" si la cartera no tiene tipo (las de ejemplo). */
export function kindLabel(p: PortfolioSummaryOut): string {
  return KIND_OPTIONS.find((o) => o.value === p.kind)?.label ?? "";
}

/** El tipo solo si añade algo al nombre (una cartera «Personal» de tipo personal no lo repite). */
export function kindSuffix(p: PortfolioSummaryOut): string {
  const label = kindLabel(p);
  return label && label.toLowerCase() !== p.name.trim().toLowerCase() ? label : "";
}
