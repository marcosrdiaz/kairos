import { useState } from "react";
import { Link } from "react-router";
import { useAlerts } from "../api/hooks/useAlerts";
import { TraceLink } from "../components/trace/TraceLink";

const DISMISSED_KEY = "kairos-alert-dismissed";

function readDismissed(): string | null {
  try {
    return sessionStorage.getItem(DISMISSED_KEY);
  } catch {
    return null; // almacenamiento bloqueado (modo privado, políticas)
  }
}

function saveDismissed(id: string): void {
  try {
    sessionStorage.setItem(DISMISSED_KEY, id);
  } catch {
    // sin almacenamiento, el aviso cerrado volverá al recargar
  }
}

interface AlertNoticeProps {
  portfolioId: string;
  /** Adónde lleva al tocarlo, conservando `?p=`. */
  href: string;
}

/**
 * Aviso en la pantalla de inicio (paso 3 del guion): el más reciente, hasta que se cierre.
 * El mensaje viene del backend, ya validado por el guardián. La región `aria-live` se monta antes
 * de que llegue el aviso para que el lector de pantalla lo anuncie.
 */
export function AlertNotice({ portfolioId, href }: AlertNoticeProps) {
  const { data } = useAlerts(portfolioId);
  const [dismissed, setDismissed] = useState(readDismissed);
  const latest = data?.[0];
  const visible = latest && latest.id !== dismissed ? latest : undefined;

  function dismiss(id: string): void {
    saveDismissed(id);
    setDismissed(id);
  }

  return (
    <div aria-live="polite" data-testid="alert-notice">
      {visible && (
        // Al llegar, el aviso abre su hueco poco a poco (la fila de la cuadrícula pasa de 0 a su
        // altura) en vez de empujar de golpe lo que hay debajo. Sin movimiento, aparece de una vez.
        <div className="grid grid-rows-[1fr] motion-safe:transition-[grid-template-rows,opacity] motion-safe:duration-500 motion-safe:ease-(--kairos-ease-out) motion-safe:starting:grid-rows-[0fr] motion-safe:starting:opacity-0">
          <div className="min-h-0 overflow-hidden">
            <div className="flex items-start gap-1 rounded-card border border-line-strong bg-surface p-1">
              <div className="flex flex-1 flex-col items-start">
                <Link
                  to={href}
                  aria-label={visible.message}
                  data-calc-id={visible.calc_id ?? undefined}
                  className="w-full rounded-control p-3 text-ink no-underline hover:bg-surface-muted"
                >
                  <span className="block text-sm font-semibold text-accent">Aviso de Kairos</span>
                  <span className="mt-0.5 block text-base leading-snug">{visible.message}</span>
                </Link>
                <TraceLink calcId={visible.calc_id} className="px-3" />
              </div>
              <button
                type="button"
                aria-label="Cerrar aviso"
                onClick={() => dismiss(visible.id)}
                className="flex size-11 shrink-0 items-center justify-center rounded-full text-xl leading-none text-ink-muted hover:bg-surface-muted"
              >
                <span aria-hidden="true">×</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
