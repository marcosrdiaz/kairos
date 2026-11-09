import { Link } from "react-router";
import type { StatusOut } from "../api/generated/schema";
import { buttonPrimary } from "../components/button";
import { ArrowRightIcon } from "../components/icons";
import { StatusBadge } from "./StatusBadge";
import { stateBandClass } from "./states";

interface StatusCardProps {
  status: StatusOut;
  /** Destino de "Ver por qué" cuando el estado tiene un motivo (evento o desvío del plan). */
  detailHref?: string;
}

/** Ilustración decorativa (barras de la marca). Sin ejes ni valores: no representa datos. */
function HeroMotif({ className }: { className: string }) {
  return (
    <svg viewBox="0 0 200 160" aria-hidden="true" focusable="false" className={className}>
      <defs>
        <linearGradient id="kairos-hero-bar" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--kairos-color-gold)" />
          <stop offset="1" stopColor="var(--kairos-color-primary)" />
        </linearGradient>
      </defs>
      {[
        [8, 96],
        [56, 72],
        [104, 48],
        [152, 20],
      ].map(([x, y]) => (
        <rect key={x} x={x} y={y} width="36" height={160 - y!} rx="6" fill="url(#kairos-hero-bar)" opacity="0.9" />
      ))}
    </svg>
  );
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
      <div className="p-6 sm:p-8 sm:pr-56 lg:p-10 lg:pr-72">
        <p className="m-0 text-base font-medium text-ink-muted">Tu cartera hoy</p>
        <div aria-live="polite" aria-atomic="true" className="mt-3">
          <StatusBadge state={status.state} label={status.state_label} />
        </div>
        <h2
          id="status-heading"
          className="mb-0 mt-5 max-w-[26ch] text-2xl font-semibold leading-tight text-ink lg:text-[2.25rem]"
        >
          {status.sentence}
        </h2>
        {hasReason && (
          <Link to={detailHref} className={`${buttonPrimary} mt-6`}>
            Ver por qué
            <ArrowRightIcon className="size-5" />
          </Link>
        )}
      </div>
      <HeroMotif className="pointer-events-none absolute bottom-0 right-8 -z-10 hidden h-36 w-44 sm:block lg:h-44 lg:w-56" />
    </section>
  );
}
