import { Link } from "react-router";
import type { StatusOut } from "../api/generated/schema";
import { buttonPrimary } from "../components/button";
import { ArrowRightIcon } from "../components/icons";
import { TraceLink } from "../components/trace/TraceLink";
import { TextMorph } from "../ui/TextMorph";
import { HeroArt } from "./HeroArt";
import { StatusBadge } from "./StatusBadge";
import { stateBandClass, withoutTapHint } from "./states";

interface StatusCardProps {
  status: StatusOut;
  /** Destino de "Ver por qué" cuando el estado tiene un motivo (evento o desvío del plan). */
  detailHref?: string;
}

/**
 * Cabecera de Inicio: estado (color + palabra), la frase del día y "Ver por qué".
 * Las cifras van en StatusTiles. Todo viene de `StatusOut`; aquí no se calcula nada.
 */
export function StatusCard({ status, detailHref = "/panel" }: StatusCardProps) {
  const hasReason = status.reason.kind !== "none";
  return (
    <section
      aria-labelledby="status-heading"
      data-calc-id={status.calc_id}
      className="relative isolate overflow-hidden rounded-card border border-line bg-linear-to-br from-accent-tint via-surface-muted to-surface"
    >
      <div className={`h-1.5 ${stateBandClass(status.state)}`} aria-hidden="true" />
      <div className="p-6 sm:w-[60%] sm:p-8 lg:p-10">
        <p className="m-0 text-base font-medium text-ink-muted">Tu cartera hoy</p>
        <div aria-live="polite" aria-atomic="true" className="mt-3">
          <StatusBadge state={status.state} label={status.state_label} />
        </div>
        <h2
          id="status-heading"
          className="mb-0 mt-5 max-w-[26ch] text-2xl font-semibold leading-tight text-ink lg:text-[2.25rem]"
        >
          <TextMorph text={withoutTapHint(status.sentence)} />
        </h2>
        <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2">
          {hasReason && (
            <Link to={detailHref} className={buttonPrimary}>
              Ver por qué
              <ArrowRightIcon className="size-5" />
            </Link>
          )}
          <TraceLink calcId={status.calc_id} />
        </div>
      </div>
      <HeroArt className="pointer-events-none absolute inset-y-0 right-0 -z-10 hidden h-full w-[52%] mask-[linear-gradient(to_right,transparent,black_35%)] sm:block" />
    </section>
  );
}
