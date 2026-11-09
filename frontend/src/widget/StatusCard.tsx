import { Link } from "react-router";
import type { StatusOut } from "../api/generated/schema";
import { formatDate, formatEur, formatPercent } from "../lib/format";
import { StatusBadge } from "./StatusBadge";
import { stateBandClass } from "./states";

interface StatusCardProps {
  status: StatusOut;
  /** Destino de "Ver por qué" cuando el estado tiene un motivo (evento o desvío del plan). */
  detailHref?: string;
}

/** "-0.015" -> "-1,5 %"; "0.012" -> "+1,2 %". El signo explícito ayuda a leer la variación. */
function signedPercent(fraction: string): string {
  const text = formatPercent(fraction);
  return fraction.trim().startsWith("-") || /^0(\.0*)?$/.test(fraction.trim()) ? text : `+${text}`;
}

/**
 * Tarjeta de estado de la cartera (pantalla de Inicio de la app).
 * Una cifra y una frase: estado (color + palabra), patrimonio, variación semanal y frase.
 * Todas las cifras vienen del backend (`StatusOut`); aquí solo se formatean.
 */
export function StatusCard({ status, detailHref = "/panel" }: StatusCardProps) {
  const hasReason = status.reason.kind !== "none";
  return (
    <section
      aria-labelledby="status-heading"
      data-calc-id={status.calc_id}
      className="overflow-hidden rounded-card border border-line bg-surface"
    >
      <div className={`h-2 ${stateBandClass(status.state)}`} aria-hidden="true" />
      <div className="flex flex-col gap-5 p-5 lg:p-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="status-heading" className="m-0 text-lg font-semibold text-ink">
            Tu cartera hoy
          </h2>
          <div aria-live="polite">
            <StatusBadge state={status.state} label={status.state_label} />
          </div>
        </div>

        <div>
          <p className="m-0 text-sm font-medium text-ink-muted">Valor total</p>
          <p className="m-0 text-hero font-semibold leading-[1.1] tabular-nums text-ink">
            {formatEur(status.total_eur)}
          </p>
          <p className="m-0 mt-1 text-base text-ink-muted">
            Esta semana:{" "}
            <span className="font-medium tabular-nums text-ink">
              {signedPercent(status.change_week_pct)}
            </span>
          </p>
        </div>

        <p className="m-0 max-w-[65ch] text-lg leading-snug text-ink">{status.sentence}</p>

        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-line pt-4">
          <p className="m-0 text-sm text-ink-muted">
            Precios a {formatDate(status.price_as_of)}
          </p>
          {hasReason && (
            <Link
              to={detailHref}
              className="inline-flex min-h-touch items-center font-medium text-accent underline"
            >
              Ver por qué
            </Link>
          )}
        </div>
      </div>
    </section>
  );
}
