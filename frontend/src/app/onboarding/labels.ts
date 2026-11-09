import type { AssetClass, AssetOut, AssetType } from "../../api/generated/schema";

export const ASSET_TYPE_LABEL: Record<AssetType, string> = {
  fund: "Fondo",
  etf: "ETF",
  stock: "Acción",
  deposit: "Depósito",
  pension_plan: "Plan de pensiones",
};

export const ASSET_CLASS_LABEL: Record<AssetClass, string> = {
  equity: "Renta variable",
  fixed_income: "Renta fija",
  cash: "Liquidez",
  mixed: "Mixto",
};

/** Orden fijo de la asignación, el mismo que en el plan. */
export const ASSET_CLASS_ORDER: AssetClass[] = ["equity", "fixed_income", "mixed", "cash"];

/** "IE00B4L5Y983 · IWDA · ETF · Renta variable · EUR" (lo que el sistema completa, RF-01). */
export function assetDetails(a: AssetOut): string {
  return [a.isin, a.ticker, ASSET_TYPE_LABEL[a.asset_type], ASSET_CLASS_LABEL[a.asset_class], a.currency]
    .filter(Boolean)
    .join(" · ");
}
