import { ApiError } from "../../api/client";
import type { DraftLine } from "./positionsDraft";

/** Mensaje para cada error del alta. El backend no guarda nada si falla una línea. */
export function submitErrorText(error: unknown, lines: DraftLine[]): string {
  if (error instanceof ApiError) {
    const assetId = typeof error.details.asset_id === "string" ? error.details.asset_id : null;
    const name = lines.find((l) => l.asset?.id === assetId)?.asset?.name ?? assetId;
    if (error.code === "NOT_FOUND" && name) {
      return `No encontramos «${name}» en el catálogo. No se ha guardado ninguna posición.`;
    }
    if (error.code === "PRICE_UNAVAILABLE") {
      return `Ahora mismo no hay precio${name ? ` de «${name}»` : ""} para valorar la cartera. No se ha guardado ninguna posición.`;
    }
    if (error.status === 422) {
      return "Alguna de las cifras no es válida. Revísalas y vuelve a guardar.";
    }
  }
  return "No hemos podido guardar las posiciones. Vuelve a intentarlo en unos segundos.";
}
