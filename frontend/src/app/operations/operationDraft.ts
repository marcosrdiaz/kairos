import type { AssetOut, TransactionRequest, TransferRequest } from "../../api/generated/schema";
import { parseDecimalInput } from "../onboarding/decimalInput";

export type OperationKind = "buy" | "sell" | "transfer";

/** Error del destino de un traspaso igual al origen (depende de los dos campos). */
export const SAME_ASSET = "El destino tiene que ser distinto del origen.";
/** Por importe en euros o por número de participaciones (el backend acepta uno de los dos). */
export type QuantityMode = "amount" | "units";

export interface OperationDraft {
  kind: OperationKind;
  mode: QuantityMode;
  /** Activo a comprar (del catálogo) o fondo de destino del traspaso. */
  asset: AssetOut | null;
  /** Posición de la cartera que se vende o desde la que se traspasa. */
  heldAssetId: string;
  quantity: string;
}

export interface DraftErrors {
  asset?: string;
  heldAssetId?: string;
  quantity?: string;
}

export type BuiltOperation =
  | { ok: true; kind: "transaction"; body: TransactionRequest }
  | { ok: true; kind: "transfer"; body: TransferRequest }
  | { ok: false; errors: DraftErrors };

export const emptyDraft = (kind: OperationKind = "buy"): OperationDraft => ({
  kind,
  mode: kind === "buy" ? "amount" : "units",
  asset: null,
  heldAssetId: "",
  quantity: "",
});

/** Participaciones con 8 decimales e importes con céntimos, como en el contrato. */
const MAX_DECIMALS: Record<QuantityMode, number> = { amount: 2, units: 8 };

/**
 * Valida el borrador y construye el cuerpo de la petición. No calcula nada: el importe o las
 * participaciones viajan tal como los escribe el usuario (normalizados a string Decimal).
 */
export function buildOperation(draft: OperationDraft): BuiltOperation {
  const errors: DraftErrors = {};
  const qty = parseDecimalInput(draft.quantity, MAX_DECIMALS[draft.mode]);
  if (!qty.ok) errors.quantity = qty.error;

  if (draft.kind === "buy" && !draft.asset) errors.asset = "Elige el activo.";
  if (draft.kind !== "buy" && !draft.heldAssetId) {
    errors.heldAssetId =
      draft.kind === "sell" ? "Elige la posición." : "Elige el fondo de origen.";
  }
  if (draft.kind === "transfer") {
    if (!draft.asset) errors.asset = "Elige el fondo de destino.";
    else if (draft.asset.id === draft.heldAssetId) {
      errors.asset = SAME_ASSET;
    }
  }
  const asset = draft.asset;
  if (!qty.ok || Object.keys(errors).length > 0) return { ok: false, errors };

  const size = draft.mode === "amount" ? { amount_eur: qty.value } : { units: qty.value };
  if (draft.kind === "transfer" && asset) {
    return {
      ok: true,
      kind: "transfer",
      body: { from_asset_id: draft.heldAssetId, to_asset_id: asset.id, ...size },
    };
  }
  if (draft.kind === "buy" && asset) {
    return { ok: true, kind: "transaction", body: { type: "buy", asset_id: asset.id, ...size } };
  }
  return {
    ok: true,
    kind: "transaction",
    body: { type: "sell", asset_id: draft.heldAssetId, ...size },
  };
}
