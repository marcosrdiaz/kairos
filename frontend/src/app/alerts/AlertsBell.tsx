import { useState, type SVGProps } from "react";
import { usePortfolioId } from "../portfolio-picker/usePortfolioId";
import { AlertsDialog } from "./AlertsDialog";
import { badgeText, bellLabel } from "./labels";
import { markRead, useReadIdsByPortfolio } from "./readStore";
import { useAllAlerts, type PortfolioAlert } from "./useAllAlerts";

/** Marca como leídos esos avisos, cada uno en su cartera. */
function markAllRead(items: readonly PortfolioAlert[]): void {
  const byPortfolio = new Map<string, string[]>();
  for (const { alert, portfolio } of items) {
    byPortfolio.set(portfolio.id, [...(byPortfolio.get(portfolio.id) ?? []), alert.id]);
  }
  for (const [portfolioId, ids] of byPortfolio) markRead(portfolioId, ids);
}

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
 * Junta los avisos de todas las carteras (T4-15): el contador es la suma de los no leídos.
 */
export function AlertsBell({ showLabel = false }: AlertsBellProps) {
  const [portfolioId] = usePortfolioId();
  const { portfolios, items, loading, failed } = useAllAlerts(portfolioId);
  const readIds = useReadIdsByPortfolio(portfolios.map((p) => p.id));
  const [open, setOpen] = useState(false);
  const isRead = (item: PortfolioAlert) =>
    readIds.get(item.portfolio.id)?.has(item.alert.id) ?? false;
  const unread = items.filter((item) => !isRead(item)).length;

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
          portfolios={portfolios}
          items={items}
          loading={loading}
          failed={failed}
          isRead={isRead}
          onMarkRead={markAllRead}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}
