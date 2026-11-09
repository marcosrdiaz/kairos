import type { ComponentType, ReactNode } from "react";
import type { StatusOut } from "../api/generated/schema";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  CalendarIcon,
  CoinsIcon,
  CompassIcon,
  TrendIcon,
} from "../components/icons";
import { TraceFigure } from "../components/trace/TraceFigure";
import { formatDate, formatEur } from "../lib/format";
import { REASON_TEXT, signedPercent, trendOf } from "./states";

type Tone = "red" | "green" | "purple" | "blue";

const TONE: Record<Tone, string> = {
  red: "bg-icon-red-bg text-icon-red",
  green: "bg-icon-green-bg text-icon-green",
  purple: "bg-icon-purple-bg text-icon-purple",
  blue: "bg-icon-blue-bg text-icon-blue",
};

interface TileProps {
  label: string;
  tone: Tone;
  Icon: ComponentType<{ className?: string }>;
  children: ReactNode;
}

/** Una pareja término/valor de la <dl>: el lector la anuncia como "Valor total: 34.311,68 €". */
function Tile({ label, tone, Icon, children }: TileProps) {
  return (
    <div className="flex flex-col gap-1 rounded-card border border-line bg-surface p-5">
      <span className={`mb-2 flex size-11 items-center justify-center rounded-control ${TONE[tone]}`}>
        <Icon className="size-6" />
      </span>
      <dt className="text-sm font-medium text-ink-muted">{label}</dt>
      <dd className="m-0 text-xl font-semibold leading-snug text-ink">{children}</dd>
    </div>
  );
}

/** Cifras del estado en tarjetas: valor, variación semanal, motivo y fecha del precio. */
export function StatusTiles({ status }: { status: StatusOut }) {
  const trend = trendOf(status.change_week_pct);
  return (
    <dl className="m-0 grid grid-cols-1 gap-4 min-[360px]:grid-cols-2 xl:grid-cols-4">
      <Tile label="Valor total" tone="red" Icon={CoinsIcon}>
        <span className="tabular-nums">
          <TraceFigure calcId={status.calc_id}>{formatEur(status.total_eur)}</TraceFigure>
        </span>
      </Tile>
      <Tile label="Esta semana" tone="green" Icon={TrendIcon}>
        <span
          className={`inline-flex items-center gap-1 tabular-nums ${trend === "up" ? "text-trend-up" : trend === "down" ? "text-trend-down" : ""}`}
        >
          {trend === "up" && <ArrowUpIcon className="size-5" />}
          {trend === "down" && <ArrowDownIcon className="size-5" />}
          <TraceFigure calcId={status.calc_id}>{signedPercent(status.change_week_pct)}</TraceFigure>
        </span>
      </Tile>
      <Tile label="Motivo del estado" tone="purple" Icon={CompassIcon}>
        {REASON_TEXT[status.reason.kind]}
      </Tile>
      <Tile label="Precios a" tone="blue" Icon={CalendarIcon}>
        {formatDate(status.price_as_of)}
      </Tile>
    </dl>
  );
}
