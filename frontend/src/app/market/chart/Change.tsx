import { ArrowDownIcon, ArrowUpIcon } from "../../../components/icons";
import { signedEur, signedPct, trendOf, type ChartRow } from "./chartFormat";

const TONE = { up: "text-trend-up", down: "text-trend-loss", flat: "text-ink-muted" } as const;

/**
 * Variación respecto al cierre anterior: flecha + signo + color (nunca solo color, DESIGN.md).
 * Subida en verde (`trend-up`); bajada en naranja (`trend-loss`: sin rojo en el mercado).
 */
export function Change({ row, compact = false }: { row: ChartRow; compact?: boolean }) {
  if (row.change === null) return <span className="text-ink-muted">—</span>;
  const trend = trendOf(row.change);
  const Icon = trend === "up" ? ArrowUpIcon : trend === "down" ? ArrowDownIcon : null;
  return (
    <span className={`inline-flex items-center gap-1 font-medium tabular-nums ${TONE[trend]}`}>
      {Icon && <Icon className="size-4 shrink-0" />}
      <span>{signedEur(row.change)}</span>
      {row.pct !== null && !compact && <span className="font-normal">({signedPct(row.pct)})</span>}
    </span>
  );
}

/** Aportación o retirada entre dos cierres, en azul informativo: explica los saltos de valor. */
export function FlowTag({ row }: { row: ChartRow }) {
  if (!row.hasFlow) return null;
  const out = row.flows.trim().startsWith("-");
  return (
    <span className="inline-flex items-center rounded-full bg-info-bg px-2 py-0.5 text-xs font-semibold text-info">
      {out ? "Retirada" : "Aportación"} {signedEur(row.flows)}
    </span>
  );
}
