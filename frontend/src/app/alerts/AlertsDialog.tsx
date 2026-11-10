import { useEffect, useId, useRef, useState } from "react";
import { useEvents } from "../../api/hooks/useEvents";
import { buttonSecondary } from "../../components/button";
import { AlertItem } from "./AlertItem";
import { emptyInboxText, INBOX_NOTICE } from "./labels";
import type { PortfolioAlert, PortfolioRef } from "./useAllAlerts";

/** Valor del filtro que muestra los avisos de todas las carteras. */
const ALL = "";

interface AlertsDialogProps {
  portfolios: readonly PortfolioRef[];
  items: readonly PortfolioAlert[];
  loading: boolean;
  failed: boolean;
  isRead: (item: PortfolioAlert) => boolean;
  onMarkRead: (items: readonly PortfolioAlert[]) => void;
  onClose: () => void;
}

/** Un aviso con el impacto de su evento, pedido a su propia cartera (la caché la comparte). */
function AlertEntry(props: {
  item: PortfolioAlert;
  showPortfolio: boolean;
  read: boolean;
  onMarkRead: () => void;
}) {
  const { item, showPortfolio, read, onMarkRead } = props;
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

/**
 * Bandeja de avisos (T2-20): hoja lateral con `<dialog>` nativo y `showModal`, como la traza.
 * Atrapa el foco, cierra con Esc o con clic en el fondo y devuelve el foco a la campana.
 * Los eventos (rango y confianza) solo se piden mientras está abierta.
 * Con varias carteras (T4-15), junta los avisos de todas, cada uno con el nombre de la suya,
 * y deja filtrar por cartera.
 */
export function AlertsDialog(props: AlertsDialogProps) {
  const { portfolios, items, loading, failed, isRead, onMarkRead, onClose } = props;
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const filterId = useId();
  const [filter, setFilter] = useState(ALL);
  const several = portfolios.length > 1;
  const shown = filter === ALL ? items : items.filter((i) => i.portfolio.id === filter);
  const unread = shown.filter((i) => !isRead(i));
  const emptyName =
    filter === ALL ? undefined : (portfolios.find((p) => p.id === filter)?.name ?? filter);

  useEffect(() => {
    if (ref.current && !ref.current.open) ref.current.showModal();
  }, []);

  const close = () => ref.current?.close();

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === event.currentTarget) close(); // clic en el fondo
      }}
      className="m-0 ml-auto h-dvh max-h-dvh w-full max-w-md overflow-y-auto border-0 border-l border-line bg-paper p-0 text-ink backdrop:bg-black/50"
    >
      <div className="flex min-h-full flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-line bg-surface px-5 py-2">
          <h2 id={titleId} className="m-0 text-xl font-semibold text-ink">
            Avisos
          </h2>
          <button
            type="button"
            aria-label="Cerrar"
            onClick={close}
            className="flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full text-2xl leading-none text-ink-muted hover:bg-surface-muted"
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>

        <div className="flex flex-1 flex-col gap-4 px-5 py-5">
          {several && (
            <div className="flex flex-col gap-2">
              <label htmlFor={filterId} className="text-base font-semibold text-ink">
                Cartera
              </label>
              <select
                id={filterId}
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
                className="min-h-touch w-full rounded-control border border-line-strong bg-surface px-3 text-base text-ink"
              >
                <option value={ALL}>Todas las carteras</option>
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          {unread.length > 0 && (
            <button
              type="button"
              className={`${buttonSecondary} self-start`}
              onClick={() => onMarkRead(unread)}
            >
              Marcar todos como leídos
            </button>
          )}
          {failed && items.length === 0 && (
            <p role="alert" className="m-0 text-base text-error">
              No hemos podido cargar los avisos. Lo volvemos a intentar en unos segundos.
            </p>
          )}
          {loading && items.length === 0 && (
            <p role="status" className="m-0 text-base text-ink-muted">
              Cargando los avisos…
            </p>
          )}
          {!loading && !(failed && items.length === 0) && shown.length === 0 && (
            <p className="m-0 text-base text-ink-muted">
              {emptyInboxText(several ? (emptyName ?? null) : undefined)}
            </p>
          )}
          {shown.length > 0 && (
            <ul className="m-0 flex list-none flex-col gap-3 p-0">
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
          <p className="m-0 mt-auto border-t border-line pt-4 text-sm text-ink-muted">
            {INBOX_NOTICE}
          </p>
        </div>
      </div>
    </dialog>
  );
}
