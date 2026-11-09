import { Link } from "react-router";
import type { StatusOut } from "../api/generated/schema";
import { LogoTile } from "../components/icons";
import { formatEur } from "../lib/format";
import { StatusBadge } from "./StatusBadge";
import { signedPercent, stateBandClass } from "./states";

interface HomeWidgetProps {
  status: StatusOut;
  /** Al tocar el widget se abre la app (Inicio), conservando `?p=`. */
  href: string;
}

/**
 * Widget de Kairos para la pantalla de inicio del móvil (simulado en web, D-004).
 * Una cifra y una frase: estado (color + palabra), valor total, variación semanal y la frase
 * completa del backend, con su "Toca para ver…" (aquí sí se toca). Todo es un único enlace.
 */
export function HomeWidget({ status, href }: HomeWidgetProps) {
  return (
    <Link
      to={href}
      data-calc-id={status.calc_id}
      aria-label={`Kairos. ${status.state_label}. ${formatEur(status.total_eur)}. ${status.sentence}`}
      className="relative block overflow-hidden rounded-[1.75rem] border border-line bg-surface/95 p-4 text-ink no-underline backdrop-blur"
    >
      <span
        className={`absolute inset-x-0 top-0 h-1 ${stateBandClass(status.state)}`}
        aria-hidden="true"
      />
      <span className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-base font-semibold">
          <LogoTile className="size-7" />
          Kairos
        </span>
        <StatusBadge state={status.state} label={status.state_label} />
      </span>
      <span className="mt-3 block text-[1.75rem] font-semibold leading-tight tabular-nums">
        {formatEur(status.total_eur)}
      </span>
      <span className="block text-sm text-ink-muted">
        Esta semana:{" "}
        <span className="tabular-nums text-ink">{signedPercent(status.change_week_pct)}</span>
      </span>
      <span className="mt-2 block text-base leading-snug">{status.sentence}</span>
    </Link>
  );
}
