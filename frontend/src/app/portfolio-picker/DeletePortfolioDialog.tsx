import { useEffect, useId, useRef } from "react";
import type { PortfolioSummaryOut } from "../../api/generated/schema";
import { buttonSecondary } from "../../components/button";

interface DeletePortfolioDialogProps {
  portfolio: PortfolioSummaryOut;
  /** Es la única cartera: al borrarla se vuelve al asistente de primer uso. */
  last: boolean;
  pending: boolean;
  error: string;
  onConfirm: () => void;
  /** Al cerrarse sin borrar (Cancelar, Esc o clic en el fondo). */
  onClose: () => void;
}

/** Botón destructivo: rojo de error del sistema (no de mercado), con su texto. */
const buttonDanger =
  "inline-flex min-h-touch items-center justify-center gap-2 rounded-full border border-error bg-error-bg px-5 text-base font-semibold text-error transition-colors hover:bg-surface";

/**
 * Confirmación de borrado (T4-13) con `<dialog>` nativo y `showModal`, como la bandeja de
 * avisos: atrapa el foco y cierra con Esc. El foco empieza en «Cancelar», la opción que no
 * destruye nada; al cerrar, el navegador lo devuelve al botón que lo abrió.
 */
export function DeletePortfolioDialog(props: DeletePortfolioDialogProps) {
  const { portfolio, last, pending, error, onConfirm, onClose } = props;
  const ref = useRef<HTMLDialogElement>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const textId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (dialog && !dialog.open) dialog.showModal();
    cancelRef.current?.focus();
  }, []);

  const close = () => ref.current?.close();

  return (
    <dialog
      ref={ref}
      role="alertdialog"
      aria-modal="true"
      aria-labelledby={titleId}
      aria-describedby={textId}
      onClose={onClose}
      onCancel={(e) => {
        if (pending) e.preventDefault(); // no se cierra a medio borrar
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !pending) close();
      }}
      className="m-auto w-[calc(100%-2rem)] max-w-md rounded-card border border-line bg-surface p-0 text-ink backdrop:bg-black/50"
    >
      <div className="flex flex-col gap-4 p-5">
        <h2 id={titleId} className="m-0 text-xl font-semibold text-ink">
          ¿Borrar «{portfolio.name}»?
        </h2>
        <p id={textId} className="m-0 text-base text-ink">
          Se borrarán sus posiciones, operaciones, aportaciones periódicas y avisos. No se puede
          deshacer.
          {last && " Es tu única cartera: después podrás crear otra desde cero."}
        </p>
        <p role="status" className="m-0 text-base font-medium text-error empty:hidden">
          {error}
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={buttonDanger}
            disabled={pending}
            aria-disabled={pending}
            onClick={onConfirm}
          >
            {pending ? "Borrando…" : "Sí, borrar"}
          </button>
          <button
            ref={cancelRef}
            type="button"
            className={buttonSecondary}
            disabled={pending}
            onClick={close}
          >
            Cancelar
          </button>
        </div>
      </div>
    </dialog>
  );
}
