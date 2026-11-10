import { apiGet, apiPost } from "../../api/client";
import type { PortfolioOut, TransactionOut } from "../../api/generated/schema";
import type { DraftPlan } from "./positionsDraft";

/**
 * Fallo a mitad del guardado: qué paso falló (`positions` = el alta con precio, que el backend
 * guarda entera o nada; `buy` = una compra), de qué activo, y qué filas ya se guardaron antes.
 */
export class SaveStepError extends Error {
  readonly step: "positions" | "buy";
  readonly assetId: string | null;
  readonly savedKeys: number[];
  constructor(step: "positions" | "buy", assetId: string | null, savedKeys: number[], cause: unknown) {
    super("save step failed", { cause });
    this.name = "SaveStepError";
    this.step = step;
    this.assetId = assetId;
    this.savedKeys = savedKeys;
  }
}

/**
 * Envía primero el alta con precio (si la hay) y después las compras por participaciones, una
 * a una (el backend las valora al último precio del proveedor y al tipo de cambio). Devuelve el
 * `PortfolioOut` del último paso; las cifras son todas del backend.
 */
export async function savePlan(portfolioId: string, plan: DraftPlan): Promise<PortfolioOut> {
  const base = `/portfolios/${encodeURIComponent(portfolioId)}`;
  const saved: number[] = [];
  let last: PortfolioOut | null = null;
  if (plan.positions.length > 0) {
    try {
      last = await apiPost<PortfolioOut>(`${base}/positions`, { positions: plan.positions }, {
        mock: "PortfolioOut",
      });
    } catch (err) {
      throw new SaveStepError("positions", null, [], err);
    }
    saved.push(...plan.positionKeys);
  }
  for (const [i, buy] of plan.buys.entries()) {
    try {
      const out = await apiPost<TransactionOut>(`${base}/transactions`, buy, { mock: "TransactionOut" });
      last = out.portfolio;
    } catch (err) {
      throw new SaveStepError("buy", buy.asset_id, [...saved], err);
    }
    const key = plan.buyKeys[i];
    if (key !== undefined) saved.push(key);
  }
  return last ?? apiGet<PortfolioOut>(base, { mock: "PortfolioOut" });
}
