import { useEffect, useId, useMemo, useRef } from "react";
import type { AlertOut, EventImpactOut } from "../../api/generated/schema";
import { useEvents } from "../../api/hooks/useEvents";
import { buttonSecondary } from "../../components/button";
import { AlertItem } from "./AlertItem";
import { INBOX_NOTICE } from "./labels";

interface AlertsDialogProps {
  portfolioId: string;
  alerts: AlertOut[] | undefined;
  loading: boolean;
  failed: boolean;
  readIds: ReadonlySet<string>;
  onMarkRead: (ids: string[]) => void;
  onClose: () => void;
}

/**
 * Bandeja de avisos (T2-20): hoja lateral con `<dialog>` nativo y `showModal`, como la traza.
 * Atrapa el foco, cierra con Esc o con clic en el fondo y devuelve el foco a la campana.
 * Los eventos (rango y confianza) solo se piden mientras está abierta.
 */
export function AlertsDialog(props: AlertsDialogProps) {
  const { portfolioId, alerts, loading, failed, readIds, onMarkRead, onClose } = props;
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const { data: events } = useEvents(portfolioId);
  const impacts = useMemo(
    () => new Map<string, EventImpactOut>((events ?? []).map((e) => [e.event_id, e])),
    [events],
  );
  const unreadIds = (alerts ?? []).filter((a) => !readIds.has(a.id)).map((a) => a.id);

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
          {unreadIds.length > 0 && (
            <button
              type="button"
              className={`${buttonSecondary} self-start`}
              onClick={() => onMarkRead(unreadIds)}
            >
              Marcar todos como leídos
            </button>
          )}
          {failed && !alerts && (
            <p role="alert" className="m-0 text-base text-error">
              No hemos podido cargar los avisos. Lo volvemos a intentar en unos segundos.
            </p>
          )}
          {loading && (
            <p role="status" className="m-0 text-base text-ink-muted">
              Cargando los avisos…
            </p>
          )}
          {alerts && alerts.length === 0 && (
            <p className="m-0 text-base text-ink-muted">
              Todavía no hay avisos de esta cartera. Te avisaremos cuando una noticia la mueva lo
              bastante.
            </p>
          )}
          {alerts && alerts.length > 0 && (
            <ul className="m-0 flex list-none flex-col gap-3 p-0">
              {alerts.map((alert) => (
                <li key={alert.id}>
                  <AlertItem
                    alert={alert}
                    impact={alert.event_id ? impacts.get(alert.event_id) : undefined}
                    read={readIds.has(alert.id)}
                    onMarkRead={(id) => onMarkRead([id])}
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
