import type { ComponentType, ReactNode } from "react";
import type { StatusOut } from "../api/generated/schema";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  CalendarIcon,
  CompassIcon,
  TrendDownIcon,
  TrendIcon,
} from "../components/icons";
import { TraceFigure } from "../components/trace/TraceFigure";
import { formatDate } from "../lib/format";
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

/**
 * Una pareja término/valor de la <dl>, en una fila compacta: icono, etiqueta y valor a la derecha.
 * El lector la anuncia como "Precios a: 6 de noviembre de 2026". El icono (decorativo) va dentro
 * del <dt>: un grupo de la <dl> solo admite <dt> y <dd>.
 */
function Tile({ label, tone, Icon, children }: TileProps) {
  return (
    <div className="flex min-w-0 grow items-center gap-3 rounded-card border border-line bg-surface px-3 py-2">
      <dt className="flex min-w-0 shrink-0 items-center gap-2.5 text-sm font-medium text-ink-muted">
        <span className={`flex size-8 shrink-0 items-center justify-center rounded-control ${TONE[tone]}`}>
          <Icon className="size-5" />
        </span>
        {label}
      </dt>
      <dd className="m-0 ml-auto min-w-0 text-right text-sm font-semibold leading-snug text-ink">
        {children}
      </dd>
    </div>
  );
}

/** Icono y tono de «Esta semana»: siguen el signo del dato que llega del backend (`trendOf`). */
const WEEK_LOOK: Record<ReturnType<typeof trendOf>, { Icon: ComponentType<{ className?: string }>; tone: Tone }> = {
  up: { Icon: TrendIcon, tone: "green" },
  down: { Icon: TrendDownIcon, tone: "red" },
  flat: { Icon: TrendIcon, tone: "blue" },
};

/** Cifras del estado en tarjetas: variación semanal, motivo y fecha del precio. */
export function StatusTiles({ status }: { status: StatusOut }) {
  const trend = trendOf(status.change_week_pct);
  const week = WEEK_LOOK[trend];
  return (
    <dl className="contents">
      <Tile label="Esta semana" tone={week.tone} Icon={week.Icon}>
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
