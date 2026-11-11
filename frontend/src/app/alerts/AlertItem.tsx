import { useId } from "react";
import type { AlertOut, EventImpactOut } from "../../api/generated/schema";
import { TraceLink } from "../../components/trace/TraceLink";
import { formatDate, formatEurRange } from "../../lib/format";
import { CONFIDENCE_LABEL } from "../news/labels";
import { kindLabel } from "./labels";
import { trendOf } from "../../widget/states";
import { ArrowDownIcon, ArrowUpIcon } from "../../components/icons";

interface AlertItemProps {
  alert: AlertOut;
  /** Impacto del evento del aviso, si sigue en la ventana de eventos (los `market_move` no tienen). */
  impact: EventImpactOut | undefined;
  /** Nombre de la cartera del aviso, si la bandeja junta varias (T4-15). */
  portfolioName?: string;
  read: boolean;
  onMarkRead: (id: string) => void;
}

/**
 * Un aviso de la bandeja: tipo, fecha, mensaje (ya validado por el guardián en el backend),
 * impacto con rango y confianza del motor de impacto, y «¿De dónde sale?».
 * «Nuevo» va en color y en palabra; las cifras no las calcula el frontend.
 */
export function AlertItem({ alert, impact, portfolioName, read, onMarkRead }: AlertItemProps) {
  const titleId = useId();
  const calcId = alert.calc_id ?? impact?.calc_id ?? null;
  const lowTrend = impact ? trendOf(impact.low_eur) : "flat";
  const highTrend = impact ? trendOf(impact.high_eur) : "flat";
  const impactTrend = lowTrend === highTrend ? lowTrend : "flat";
  const impactClass =
    impactTrend === "up"
      ? "text-trend-up"
      : impactTrend === "down"
        ? "text-trend-down"
        : "text-ink";
  return (
    <article
      aria-labelledby={titleId}
      data-calc-id={calcId ?? undefined}
      className={`flex flex-col gap-2 rounded-card border p-4 ${read ? "border-line bg-surface" : "border-line-strong bg-surface-muted"}`}
    >
      <div className="flex flex-wrap items-start gap-3">
        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-3 gap-y-1">
          {!read && (
            <span className="rounded-full bg-accent-tint px-2 py-0.5 text-sm font-semibold text-accent">
              Nuevo
            </span>
          )}
          <h3 id={titleId} className="m-0 text-base font-semibold text-ink">
            {kindLabel(alert.kind)}
          </h3>
          <time dateTime={alert.created_at} className="text-sm text-ink-muted">
            {formatDate(alert.created_at)}
          </time>
        </div>
        {!read && (
          <button
            type="button"
            onClick={() => onMarkRead(alert.id)}
            className="ml-auto inline-flex min-h-touch shrink-0 cursor-pointer items-center gap-2 rounded-control border border-line-strong bg-surface px-3 text-sm font-semibold text-success transition-colors hover:bg-success-bg focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-focus active:scale-95 motion-reduce:transition-none"
          >
            <svg
              aria-hidden="true"
              focusable="false"
              viewBox="0 0 24 24"
              className="size-5"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m5 12 4 4L19 6" />
            </svg>
            Marcar como leído
          </button>
        )}
      </div>
      {portfolioName && (
        <p className="m-0 text-sm font-medium text-ink-muted">Cartera «{portfolioName}»</p>
      )}
      <p className="m-0 text-base leading-snug text-ink">{alert.message}</p>
      {impact && (
        <p className="m-0 text-sm text-ink-muted">
          Impacto estimado en {portfolioName ? "esta cartera" : "tu cartera"}:{" "}
          <span className={`inline-flex items-center gap-1 font-semibold tabular-nums ${impactClass}`}>
            {impactTrend === "up" && <ArrowUpIcon className="size-4 shrink-0" />}
            {impactTrend === "down" && <ArrowDownIcon className="size-4 shrink-0" />}
            {formatEurRange(impact.low_eur, impact.high_eur)}
          </span>
          {" · "}
          {CONFIDENCE_LABEL[impact.confidence]}
        </p>
      )}
      <div className="flex flex-wrap items-center gap-x-5">
        <TraceLink calcId={calcId} />
      </div>
    </article>
  );
}
