import { ApiError } from "../../api/client";
import type { DraftLine } from "./positionsDraft";
import { SaveStepError } from "./savePositions";

/**
 * Mensaje para cada error del alta. El alta con precio no guarda nada si falla una línea; las
 * compras van una a una, así que si falla una, las anteriores ya están guardadas.
 */
export function submitErrorText(error: unknown, lines: DraftLine[]): string {
  const step = error instanceof SaveStepError ? error : null;
  const cause = step ? step.cause : error;
  const savedBefore = (step?.savedKeys.length ?? 0) > 0;
  const outcome = savedBefore
    ? "Las posiciones anteriores sí se han guardado y ya no aparecen aquí."
    : "No se ha guardado ninguna posición.";
  if (cause instanceof ApiError) {
    const fromDetails = typeof cause.details.asset_id === "string" ? cause.details.asset_id : null;
    const assetId = fromDetails ?? step?.assetId ?? null;
    const name = lines.find((l) => l.asset?.id === assetId)?.asset?.name ?? assetId;
    if (cause.code === "NOT_FOUND" && name) {
      return `No encontramos «${name}» en el catálogo. ${outcome}`;
    }
    if (cause.code === "PRICE_UNAVAILABLE") {
      if (step?.step === "buy") {
        return `Ahora mismo no hay precio${name ? ` de «${name}»` : ""} para registrarla al precio de hoy. Indica el precio de compra en su fila o vuelve a intentarlo más tarde. ${outcome}`;
      }
      return `Ahora mismo no hay precio${name ? ` de «${name}»` : ""} para valorar la cartera. ${outcome}`;
    }
    if (cause.status === 422) {
      return `Alguna de las cifras no es válida. Revísalas y vuelve a guardar.${savedBefore ? ` ${outcome}` : ""}`;
    }
  }
  return `No hemos podido guardar las posiciones. Vuelve a intentarlo en unos segundos.${savedBefore ? ` ${outcome}` : ""}`;
}
