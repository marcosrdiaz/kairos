import { useState, type SVGProps } from "react";
import { useAlerts } from "../../api/hooks/useAlerts";
import { usePortfolioId } from "../portfolio-picker/usePortfolioId";
import { AlertsDialog } from "./AlertsDialog";
import { badgeText, bellLabel } from "./labels";
import { markRead, useReadIds } from "./readStore";

/** Campana, decorativa: el significado lo da el nombre accesible del botón. */
function BellIcon(props: Omit<SVGProps<SVGSVGElement>, "children">) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      <path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z" />
      <path d="M10 20.5a2 2 0 0 0 4 0" />
    </svg>
  );
}

interface AlertsBellProps {
  /** Con texto «Avisos» (barra lateral de escritorio). Si no, solo icono (cabecera móvil). */
  showLabel?: boolean;
}

/**
 * Campana de avisos con el número de no leídos (T2-20). Los avisos llegan por el polling de
 * `useAlerts` (5 s, T2-13), así que el contador cambia solo tras un replay. No anuncia el
 * cambio: ya lo hace el aviso de Inicio (`widget/AlertNotice`), y duplicarlo sería ruido.
 */
export function AlertsBell({ showLabel = false }: AlertsBellProps) {
  const [portfolioId] = usePortfolioId();
  const { data: alerts, isPending, isError } = useAlerts(portfolioId);
  const readIds = useReadIds(portfolioId);
  const [open, setOpen] = useState(false);
  const unread = (alerts ?? []).filter((a) => !readIds.has(a.id)).length;

  return (
    <>
      <button
        type="button"
        aria-label={bellLabel(unread)}
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
        className={[
          "relative inline-flex min-h-touch min-w-touch cursor-pointer items-center gap-2.5 rounded-control text-base font-medium text-ink",
          showLabel
            ? "w-full justify-start px-3 hover:bg-surface"
            : "justify-center border border-line bg-surface px-2.5 hover:border-line-strong",
        ].join(" ")}
      >
        <BellIcon className="size-5 shrink-0" />
        {showLabel && <span aria-hidden="true">Avisos</span>}
        {unread > 0 && (
          <span
            aria-hidden="true"
            data-testid="alerts-badge"
            className={[
              "inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-accent px-1.5 text-xs font-semibold leading-none text-on-accent",
              showLabel ? "ml-auto" : "absolute -right-1.5 -top-1.5",
            ].join(" ")}
          >
            {badgeText(unread)}
          </span>
        )}
      </button>
      {open && (
        <AlertsDialog
          portfolioId={portfolioId}
          alerts={alerts}
          loading={isPending}
          failed={isError}
          readIds={readIds}
          onMarkRead={(ids) => markRead(portfolioId, ids)}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}
