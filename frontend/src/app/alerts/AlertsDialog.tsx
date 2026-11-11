import { useEffect, useId, useRef } from "react";
import { AlertsInbox, type AlertsInboxProps } from "./AlertsInbox";

interface AlertsDialogProps extends AlertsInboxProps {
  onClose: () => void;
}

/** Bandeja histórica, compartiendo contenido con la nueva ruta integrada de Avisos. */
export function AlertsDialog({ onClose, ...inbox }: AlertsDialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

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
        if (event.target === event.currentTarget) close();
      }}
      className="m-0 ml-auto h-dvh max-h-dvh w-full max-w-md overflow-y-auto border-0 border-l border-line bg-paper p-0 text-ink backdrop:bg-black/50"
    >
      <div className="flex min-h-full flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-line bg-surface px-5 py-2">
          <h2 id={titleId} className="m-0 text-xl font-semibold text-ink">Avisos</h2>
          <button
            type="button"
            aria-label="Cerrar"
            onClick={close}
            className="flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full text-2xl leading-none text-ink-muted hover:bg-surface-muted"
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>
        <div className="flex-1 px-5 py-5"><AlertsInbox {...inbox} /></div>
      </div>
    </dialog>
  );
}
