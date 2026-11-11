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
      className="flex min-w-0 flex-col rounded-card border border-line bg-surface p-5"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="flex size-11 items-center justify-center rounded-control bg-icon-red-bg text-icon-red">
          <CoinsIcon className="size-6" />
        </span>
        <span className={`mt-1 h-1.5 w-10 rounded-full ${stateBandClass(status.state)}`} aria-hidden="true" />
      </div>
      <p className="m-0 mt-3 text-sm font-medium text-ink-muted">Tu cartera hoy</p>
      <p className="m-0 mt-1 text-xl font-semibold tabular-nums text-ink">
        <TraceFigure calcId={status.calc_id}>{formatEur(status.total_eur)}</TraceFigure>
      </p>
      <div aria-live="polite" aria-atomic="true" className="mt-3">
        <StatusBadge state={status.state} label={status.state_label} />
      </div>
      <h2
        id="status-heading"
        className="mb-0 mt-3 text-base font-medium leading-snug text-ink"
      >
        <TextMorph text={withoutTapHint(status.sentence)} />
      </h2>
      <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-2 pt-3">
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
