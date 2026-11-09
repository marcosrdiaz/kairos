import type { ReactNode, Ref } from "react";
import type { TransactionOut } from "../../api/generated/schema";
import { TraceFigure } from "../../components/trace/TraceFigure";
import { formatDate, formatEur, formatUnits } from "../../lib/format";
import { findPosition, formatPrice } from "./usePortfolio";

const TITLE: Record<TransactionOut["type"], string> = {
  buy: "Compra registrada",
  sell: "Venta registrada",
  transfer: "Traspaso registrado",
  dca_buy: "Aportación registrada",
};

/** Toda cifra lleva su `calc_id` (regla 4): el de la operación o, si sale de la cartera, el suyo. */
function Row({ label, children, calcId }: { label: string; children: ReactNode; calcId: string }) {
  return (
    <>
      <dt className="text-ink-muted">{label}</dt>
      <dd className="m-0 font-semibold text-ink tabular-nums" data-calc-id={calcId}>
        <TraceFigure calcId={calcId}>{children}</TraceFigure>
      </dd>
    </>
  );
}

interface OperationResultProps {
  tx: TransactionOut;
  /** Nombre del activo conocido al enviar, por si ya no está en la cartera (venta total). */
  fallbackName?: string | null;
  fallbackToName?: string | null;
  ref?: Ref<HTMLElement>;
}

/**
 * Lo que devuelve el backend tras registrar (UC-03, paso 3): precio usado y su fecha, y el
 * efecto (participaciones, precio medio o plusvalía estimada). Ninguna cifra se calcula aquí;
 * `data-calc-id` apunta a la traza para el "¿De dónde sale?".
 */
export function OperationResult({ tx, fallbackName, fallbackToName, ref }: OperationResultProps) {
  const p = tx.portfolio;
  const name = findPosition(p, tx.asset_id)?.name ?? fallbackName ?? tx.asset_id;
  const toName = tx.to_asset_id
    ? (findPosition(p, tx.to_asset_id)?.name ?? fallbackToName ?? tx.to_asset_id)
    : null;
  const toPosition = tx.to_asset_id ? findPosition(p, tx.to_asset_id) : undefined;
  const gain = tx.effect.realized_gain_eur;
  return (
    <section
      ref={ref}
      tabIndex={-1}
      aria-labelledby="operation-result-title"
      data-calc-id={tx.calc_id}
      className="flex flex-col gap-4 rounded-card border border-line bg-surface-muted p-5"
    >
      <h3 id="operation-result-title" className="m-0 text-lg font-semibold text-success">
        {TITLE[tx.type]}
      </h3>
      <p className="m-0 text-ink">
        {toName ? (
          <>
            De «{name}» a «{toName}». Se conservan el coste y la fecha de compra de cada lote, así
            que no tributa ahora.
          </>
        ) : (
          <>«{name}»</>
        )}
      </p>
      <dl className="m-0 grid gap-x-6 gap-y-3 sm:grid-cols-[auto_1fr]">
        <Row label="Participaciones" calcId={tx.calc_id}>
          {formatUnits(tx.units)}
        </Row>
        <Row label="Importe" calcId={tx.calc_id}>
          {formatEur(tx.amount_eur)}
        </Row>
        <Row label="Precio usado" calcId={tx.calc_id}>
          {formatPrice(tx.price, tx.price_currency)}{" "}
          <span className="font-normal text-ink-muted">del {formatDate(tx.price_at)}</span>
        </Row>
        {gain != null && (
          <Row label={gain.startsWith("-") ? "Minusvalía estimada" : "Plusvalía estimada"} calcId={tx.calc_id}>
            {formatEur(gain)}
          </Row>
        )}
        <Row label={toName ? `Te quedan en «${name}»` : "Participaciones ahora"} calcId={tx.calc_id}>
          {formatUnits(tx.effect.units_after)}
        </Row>
        {tx.type !== "sell" && !toName && (
          <Row label="Precio medio ahora" calcId={tx.calc_id}>
            {formatEur(tx.effect.avg_cost_eur_after)}
          </Row>
        )}
        {toPosition && (
          <Row label={`Ahora en «${toPosition.name}»`} calcId={p.calc_id}>
            {formatUnits(toPosition.units)}
          </Row>
        )}
        <Row label="Valor de la cartera" calcId={p.calc_id}>
          {formatEur(p.total_eur)}
        </Row>
      </dl>
      {gain != null && (
        <p className="m-0 text-sm text-ink-muted">
          La plusvalía es una estimación con el método FIFO: se venden primero las participaciones
          más antiguas.
        </p>
      )}
    </section>
  );
}
