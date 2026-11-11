import { useId, useState } from "react";
import { useEvents } from "../../api/hooks/useEvents";
import { buttonSecondary } from "../../components/button";
import { AlertItem } from "./AlertItem";
import { emptyInboxText, INBOX_NOTICE } from "./labels";
import type { PortfolioAlert, PortfolioRef } from "./useAllAlerts";

export interface AlertsInboxProps {
  portfolios: readonly PortfolioRef[];
  items: readonly PortfolioAlert[];
  loading: boolean;
  failed: boolean;
  isRead: (item: PortfolioAlert) => boolean;
  onMarkRead: (items: readonly PortfolioAlert[]) => void;
}

function AlertEntry({ item, showPortfolio, read, onMarkRead }: {
  item: PortfolioAlert;
  showPortfolio: boolean;
  read: boolean;
  onMarkRead: () => void;
}) {
  const { data: events } = useEvents(item.portfolio.id);
  const eventId = item.alert.event_id;
  const impact = eventId ? events?.find((e) => e.event_id === eventId) : undefined;
  return (
    <AlertItem
      alert={item.alert}
      impact={impact}
      portfolioName={showPortfolio ? item.portfolio.name : undefined}
      read={read}
      onMarkRead={onMarkRead}
    />
  );
}

/** Lista y filtros compartidos por la página de Avisos y la bandeja anterior. */
export function AlertsInbox({ portfolios, items, loading, failed, isRead, onMarkRead }: AlertsInboxProps) {
  const filterId = useId();
  const [filter, setFilter] = useState("");
  const several = portfolios.length > 1;
  const shown = filter === "" ? items : items.filter((i) => i.portfolio.id === filter);
  const unread = shown.filter((i) => !isRead(i));
  const emptyName = filter === "" ? undefined : (portfolios.find((p) => p.id === filter)?.name ?? filter);

  return (
    <div className="flex flex-col gap-4">
      {several && (
        <div className="flex flex-col gap-2">
          <label htmlFor={filterId} className="text-base font-semibold text-ink">Cartera</label>
          <select
            id={filterId}
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            className="min-h-touch w-full rounded-control border border-line-strong bg-surface px-3 text-base text-ink sm:max-w-sm"
          >
            <option value="">Todas las carteras</option>
            {portfolios.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>
      )}
      {unread.length > 0 && (
        <button type="button" className={`${buttonSecondary} self-start`} onClick={() => onMarkRead(unread)}>
          Marcar todos como leídos
        </button>
      )}
      {failed && items.length === 0 && (
        <p role="alert" className="m-0 text-base text-error">
          No hemos podido cargar los avisos. Lo volvemos a intentar en unos segundos.
        </p>
      )}
      {loading && items.length === 0 && <p role="status" className="m-0 text-base text-ink-muted">Cargando los avisos…</p>}
      {!loading && !(failed && items.length === 0) && shown.length === 0 && (
        <p className="m-0 text-base text-ink-muted">{emptyInboxText(several ? (emptyName ?? null) : undefined)}</p>
      )}
      {shown.length > 0 && (
        <ul className="m-0 grid list-none gap-3 p-0 xl:grid-cols-2">
          {shown.map((item) => (
            <li key={`${item.portfolio.id}:${item.alert.id}`}>
              <AlertEntry
                item={item}
                showPortfolio={several}
                read={isRead(item)}
                onMarkRead={() => onMarkRead([item])}
              />
            </li>
          ))}
        </ul>
      )}
      <p className="m-0 border-t border-line pt-4 text-sm text-ink-muted">{INBOX_NOTICE}</p>
    </div>
  );
}
