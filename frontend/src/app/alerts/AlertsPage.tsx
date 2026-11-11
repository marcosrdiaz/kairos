import { usePortfolioId } from "../portfolio-picker/usePortfolioId";
import { PageTitle } from "../../components/PageTitle";
import { AlertsInbox } from "./AlertsInbox";
import { markRead, useReadIdsByPortfolio } from "./readStore";
import { useAllAlerts, type PortfolioAlert } from "./useAllAlerts";

function markAllRead(items: readonly PortfolioAlert[]): void {
  const byPortfolio = new Map<string, string[]>();
  for (const { alert, portfolio } of items) {
    byPortfolio.set(portfolio.id, [...(byPortfolio.get(portfolio.id) ?? []), alert.id]);
  }
  for (const [portfolioId, ids] of byPortfolio) markRead(portfolioId, ids);
}

/** Avisos como pantalla integrada: conserva datos, filtros y estado de lectura por cartera. */
export function AlertsPage() {
  const [portfolioId] = usePortfolioId();
  const { portfolios, items, loading, failed } = useAllAlerts(portfolioId);
  const readIds = useReadIdsByPortfolio(portfolios.map((p) => p.id));
  const isRead = (item: PortfolioAlert) => readIds.get(item.portfolio.id)?.has(item.alert.id) ?? false;

  return (
    <section className="flex w-full min-w-0 flex-col gap-6" aria-label="Avisos">
      <PageTitle>Avisos</PageTitle>
      <AlertsInbox
        portfolios={portfolios}
        items={items}
        loading={loading}
        failed={failed}
        isRead={isRead}
        onMarkRead={markAllRead}
      />
    </section>
  );
}
