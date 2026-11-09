import { ApiError } from "../../api/client";
import type { AssetType } from "../../api/generated/schema";
import { formatUnits } from "../../lib/format";
import type { OperationKind } from "./operationDraft";

const str = (v: unknown): string | null => (typeof v === "string" && v !== "" ? v : null);

/** `details` de 422 `TRANSFER_NOT_ALLOWED` (D-062). Las cifras pueden venir a null. */
export interface TransferNotAllowed {
  fromType: AssetType | null;
  toType: AssetType | null;
  estimatedGainEur: string | null;
  calcId: string | null;
}

export function transferNotAllowed(error: unknown): TransferNotAllowed | null {
  if (!(error instanceof ApiError) || error.code !== "TRANSFER_NOT_ALLOWED") return null;
  const d = error.details;
  return {
    fromType: str(d.from_asset_type) as AssetType | null,
    toType: str(d.to_asset_type) as AssetType | null,
    estimatedGainEur: str(d.estimated_gain_eur),
    calcId: str(d.calc_id),
  };
}

const NOTHING = "No se ha registrado nada.";

/**
 * Mensaje para cada error de una operación. Las cifras que aparecen (participaciones
 * disponibles) son las que devuelve el backend en `details`, solo formateadas.
 */
export function operationErrorText(error: unknown, kind: OperationKind, assetLabel: string | null): string {
  if (error instanceof ApiError) {
    const of = assetLabel ? ` de «${assetLabel}»` : "";
    if (error.code === "INSUFFICIENT_UNITS") {
      const available = str(error.details.available_units);
      return available
        ? `No hay tantas participaciones${of}: en la cartera hay ${formatUnits(available)}. ${NOTHING}`
        : `No hay tantas participaciones${of} en la cartera. ${NOTHING}`;
    }
    if (error.code === "PRICE_UNAVAILABLE") {
      return `Ahora mismo no hay precio${of} para registrar la operación. ${NOTHING}`;
    }
    if (error.code === "NOT_FOUND") {
      // El backend dice qué falta en `details` (portfolio/errors.py): `asset_id` o `portfolio_id`.
      if (str(error.details.asset_id)) return `No encontramos ese activo en el catálogo. ${NOTHING}`;
      if (str(error.details.portfolio_id)) return `No encontramos esta cartera. ${NOTHING}`;
      return `No encontramos lo necesario para registrar la operación. ${NOTHING}`;
    }
    if (error.code === "mock_missing") {
      return "En el modo de ejemplo no hay respuesta para esta operación.";
    }
    if (error.status === 422) {
      return kind === "transfer"
        ? `Revisa el origen, el destino y la cantidad del traspaso. ${NOTHING}`
        : `Revisa el activo y la cantidad. ${NOTHING}`;
    }
  }
  return `No hemos podido registrar la operación. Vuelve a intentarlo en unos segundos. ${NOTHING}`;
}
