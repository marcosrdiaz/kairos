import { useId } from "react";
import type { AlertOut, EventImpactOut } from "../../api/generated/schema";
import { TraceLink } from "../../components/trace/TraceLink";
import { formatDate, formatEurRange } from "../../lib/format";
import { CONFIDENCE_LABEL } from "../news/labels";
import { kindLabel } from "./labels";

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
  return (
    <article
      aria-labelledby={titleId}
      data-calc-id={calcId ?? undefined}
      className={`flex flex-col gap-2 rounded-card border p-4 ${read ? "border-line bg-surface" : "border-line-strong bg-surface-muted"}`}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
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
      {portfolioName && (
        <p className="m-0 text-sm font-medium text-ink-muted">Cartera «{portfolioName}»</p>
      )}
      <p className="m-0 text-base leading-snug text-ink">{alert.message}</p>
      {impact && (
        <p className="m-0 text-sm text-ink-muted">
          Impacto estimado en {portfolioName ? "esta cartera" : "tu cartera"}: {formatEurRange(impact.low_eur, impact.high_eur)} ·{" "}
          {CONFIDENCE_LABEL[impact.confidence]}
        </p>
      )}
      <div className="flex flex-wrap items-center gap-x-5">
        <TraceLink calcId={calcId} />
        {!read && (
          <button
            type="button"
            onClick={() => onMarkRead(alert.id)}
            className="inline-flex min-h-touch cursor-pointer items-center border-0 bg-transparent p-0 text-base font-medium text-ink-muted underline hover:text-ink"
          >
            Marcar como leído
          </button>
        )}
      </div>
    </article>
  );
}
