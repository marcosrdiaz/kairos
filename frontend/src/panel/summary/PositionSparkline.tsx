import { useAssetHistory } from "../../api/hooks/useAssetHistory";
import type { AssetHistoryPoint } from "../../api/generated/schema";
import { formatPrice } from "../../app/operations/usePortfolio";
import { Sparkline } from "../../ui/Sparkline";

/** Periodo de la columna «Evolución». Misma clave de caché que `/activo/:id` con ese periodo. */
export const SPARKLINE_PERIOD = "1m" as const;

const hasPrice = (p: Partial<AssetHistoryPoint>): p is AssetHistoryPoint =>
  typeof p.price === "string" && Number.isFinite(Number(p.price));

/**
 * Minigráfico del precio de una posición en el último mes (T5-04). Dibuja el precio de cierre
 * (VL en los fondos), no el valor en euros, para que una compra o una venta no parezca una
 * subida o una bajada. No muestra ninguna variación: la API no da la del periodo (`change_pct`
 * de cada punto es respecto al cierre anterior) y no se calcula en el cliente. El resumen para
 * lectores de pantalla usa los precios tal como llegan de la API.
 */
export function PositionSparkline({
  portfolioId,
  assetId,
  name,
}: {
  portfolioId: string;
  assetId: string;
  name: string;
}) {
  const { data, isPending, isError } = useAssetHistory(portfolioId, assetId, SPARKLINE_PERIOD);

  if (isPending) {
    return (
      <span
        aria-hidden="true"
        className="inline-block h-8 w-[120px] rounded bg-surface-muted align-middle motion-safe:animate-pulse"
      />
    );
  }

  const points = isError || !data ? [] : (data.points as Partial<AssetHistoryPoint>[]).filter(hasPrice);
  const first = points[0];
  const last = points.at(-1);
  if (!data || first === undefined || last === undefined) {
    return <span className="text-sm text-ink-muted">Sin datos</span>;
  }

  const label =
    `Precio de ${name} en el último mes: ${points.length} cierres, ` +
    `de ${formatPrice(first.price, data.currency)} a ${formatPrice(last.price, data.currency)}`;

  return <Sparkline values={points.map((p) => Number(p.price))} label={label} className="align-middle" />;
}
