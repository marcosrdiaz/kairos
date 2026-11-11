import { usePortfolioId } from "../portfolio-picker/usePortfolioId";
import { badgeText } from "./labels";
import { useReadIdsByPortfolio } from "./readStore";
import { useAllAlerts } from "./useAllAlerts";

/** Icono de la ruta Avisos con contador; el texto del enlace sigue siendo «Avisos». */
export function AlertsNavIcon({ className }: { className?: string }) {
  const [portfolioId] = usePortfolioId();
  const { portfolios, items } = useAllAlerts(portfolioId);
  const readIds = useReadIdsByPortfolio(portfolios.map((p) => p.id));
  const unread = items.filter((item) => !readIds.get(item.portfolio.id)?.has(item.alert.id)).length;

  return (
    <span className="relative inline-flex shrink-0" aria-hidden="true">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
        focusable="false"
      >
        <path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z" />
        <path d="M10 20.5a2 2 0 0 0 4 0" />
      </svg>
      {unread > 0 && (
        <span data-testid="alerts-badge" className="absolute -right-2 -top-2 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-brand-red px-1 text-[0.625rem] font-bold leading-none text-paper">
          {badgeText(unread)}
        </span>
      )}
    </span>
  );
}
