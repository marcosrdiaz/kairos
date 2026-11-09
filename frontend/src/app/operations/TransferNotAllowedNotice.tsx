import type { Ref } from "react";
import type { AssetType } from "../../api/generated/schema";
import { buttonSecondary } from "../../components/button";
import { TraceFigure } from "../../components/trace/TraceFigure";
import { formatEur } from "../../lib/format";
import type { TransferNotAllowed } from "./operationError";

const WITH_ARTICLE: Record<AssetType, string> = {
  fund: "un fondo",
  etf: "un ETF",
  stock: "una acción",
  deposit: "un depósito",
  pension_plan: "un plan de pensiones",
};

function whyNot({ fromType, toType }: TransferNotAllowed): string {
  const parts: string[] = [];
  if (fromType && fromType !== "fund") parts.push(`el origen es ${WITH_ARTICLE[fromType]}`);
  if (toType && toType !== "fund") parts.push(`el destino es ${WITH_ARTICLE[toType]}`);
  if (parts.length === 0) return "";
  const text = parts.join(" y ");
  return ` Aquí ${text}.`;
}

interface TransferNotAllowedNoticeProps {
  info: TransferNotAllowed;
  onSellInstead: () => void;
  ref?: Ref<HTMLDivElement>;
}

/**
 * Explicación fiscal de `TRANSFER_NOT_ALLOWED` (RF-06, UC-03 alternativo): por qué no hay
 * traspaso y qué supone la alternativa (venta + compra) con la plusvalía estimada que da el
 * backend. Describe el hecho fiscal; no recomienda ninguna de las dos opciones.
 */
export function TransferNotAllowedNotice({ info, onSellInstead, ref }: TransferNotAllowedNoticeProps) {
  const gain = info.estimatedGainEur;
  const isLoss = gain?.startsWith("-") ?? false;
  return (
    <div
      ref={ref}
      tabIndex={-1}
      role="alert"
      className="flex flex-col gap-3 rounded-card border border-line-strong bg-info-bg p-5 text-ink"
    >
      <h3 className="m-0 text-lg font-semibold">Este traspaso no se puede registrar</h3>
      <p className="m-0">
        Solo los traspasos entre fondos de inversión aplazan los impuestos.{whyNot(info)} No se ha
        registrado nada.
      </p>
      <p className="m-0">
        La alternativa es registrar una venta del origen y después una compra del destino. La
        venta sí tributa:{" "}
        {gain ? (
          <>
            con el precio de ahora, la {isLoss ? "minusvalía" : "plusvalía"} estimada de esas
            participaciones es de{" "}
            <strong className="tabular-nums">
              <TraceFigure calcId={info.calcId}>{formatEur(gain)}</TraceFigure>
            </strong>
            .
          </>
        ) : (
          "ahora mismo no podemos estimar su plusvalía (falta el precio o no hay tantas participaciones)."
        )}
      </p>
      <button type="button" className={`${buttonSecondary} self-start`} onClick={onSellInstead}>
        Registrar como venta
      </button>
    </div>
  );
}
