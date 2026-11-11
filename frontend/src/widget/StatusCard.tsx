import { Link } from "react-router";
import type { StatusOut } from "../api/generated/schema";
import { buttonPrimary } from "../components/button";
import { ArrowRightIcon, CoinsIcon } from "../components/icons";
import { TraceLink } from "../components/trace/TraceLink";
import { TraceFigure } from "../components/trace/TraceFigure";
import { formatEur } from "../lib/format";
import { TextMorph } from "../ui/TextMorph";
import { StatusBadge } from "./StatusBadge";
import { stateBandClass, withoutTapHint } from "./states";

interface StatusCardProps {
  status: StatusOut;
  /** Destino de "Ver por qué" cuando el estado tiene un motivo (evento o desvío del plan). */
  detailHref?: string;
}

/**
 * «Tu cartera hoy» ocupa el lugar de la tarjeta de valor total. Estado, cifra y frase
 * vienen de `StatusOut`; aquí no se calcula nada.
 */
export function StatusCard({ status, detailHref = "/panel" }: StatusCardProps) {
  const hasReason = status.reason.kind !== "none";
  return (
    <section
      aria-labelledby="status-heading"
      data-calc-id={status.calc_id}
      className="flex min-w-0 grow flex-col gap-2 rounded-card border border-line bg-surface p-4"
    >
      <div className="flex items-center gap-3">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-control bg-icon-red-bg text-icon-red">
          <CoinsIcon className="size-5" />
        </span>
        <p className="m-0 min-w-0 flex-1 text-sm font-medium text-ink-muted">Tu cartera hoy</p>
        <div aria-live="polite" aria-atomic="true">
          <StatusBadge state={status.state} label={status.state_label} />
        </div>
      </div>
      <p className="m-0 text-3xl font-semibold leading-none tabular-nums text-ink">
        <TraceFigure calcId={status.calc_id}>{formatEur(status.total_eur)}</TraceFigure>
      </p>
      <span className={`h-1 w-full rounded-full ${stateBandClass(status.state)}`} aria-hidden="true" />
      <h2 id="status-heading" className="m-0 text-base font-medium leading-snug text-ink">
        <TextMorph text={withoutTapHint(status.sentence)} />
      </h2>
      <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-1">
        {hasReason && (
          <Link to={detailHref} className={buttonPrimary}>
            Ver por qué
            <ArrowRightIcon className="size-5" />
          </Link>
        )}
        <TraceLink calcId={status.calc_id} />
      </div>
    </section>
  );
}
