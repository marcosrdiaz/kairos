import { useRef, useState } from "react";
import type { PortfolioSummaryOut } from "../../api/generated/schema";
import { useDeletePortfolio } from "../../api/hooks/usePortfolioManage";
import { buttonPrimary } from "../../components/button";
import { DeletePortfolioDialog } from "./DeletePortfolioDialog";
import { NewPortfolioForm } from "./NewPortfolioForm";
import { PortfolioRow } from "./PortfolioRow";
import { usePortfolioId } from "./usePortfolioId";
import { usePortfolios } from "./usePortfolios";

/**
 * Gestión de las carteras en Cartera (T4-13): lista con renombrar y borrar, y «Nueva cartera».
 * Al crear una, pasa a ser la elegida. Al borrar la elegida, `useSyncPortfolioId` elige otra;
 * si era la última, la lista queda vacía y `FirstRunGate` abre el asistente de primer uso.
 * Cada cambio se anuncia en una región de estado.
 */
export function PortfolioManager() {
  const { data } = usePortfolios();
  const [current, select] = usePortfolioId();
  const remove = useDeletePortfolio();
  const [creating, setCreating] = useState(false);
  const [toDelete, setToDelete] = useState<PortfolioSummaryOut | null>(null);
  const [message, setMessage] = useState("");
  const newButtonRef = useRef<HTMLButtonElement>(null);
  const listTitleRef = useRef<HTMLHeadingElement>(null);
  const list = data ?? [];

  function created(p: PortfolioSummaryOut, imported: boolean) {
    setCreating(false);
    select(p.id);
    setMessage(
      imported
        ? `Cartera «${p.name}» importada. Ahora estás viendo esta.`
        : `Cartera «${p.name}» creada. Ahora estás viendo esta.`,
    );
    requestAnimationFrame(() => newButtonRef.current?.focus());
  }

  function confirmDelete() {
    if (!toDelete) return;
    const gone = toDelete;
    remove.mutate(gone.id, {
      onSuccess: () => {
        setToDelete(null);
        const rest = list.filter((p) => p.id !== gone.id);
        const next = gone.id === current ? rest[0] : rest.find((p) => p.id === current);
        if (gone.id === current && next) select(next.id);
        setMessage(
          next && gone.id === current
            ? `Cartera «${gone.name}» borrada. Ahora estás viendo «${next.name}».`
            : `Cartera «${gone.name}» borrada.`,
        );
        requestAnimationFrame(() => listTitleRef.current?.focus());
      },
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <h3
        ref={listTitleRef}
        tabIndex={-1}
        className="m-0 text-lg font-semibold text-ink outline-none"
      >
        Tus carteras
      </h3>
      {list.length > 0 && (
        <ul aria-label="Tus carteras" className="m-0 flex list-none flex-col gap-2 p-0">
          {list.map((p) => (
            <PortfolioRow
              key={p.id}
              portfolio={p}
              selected={p.id === current}
              onRenamed={(before, after) => setMessage(`«${before}» ahora se llama «${after}».`)}
              onDelete={() => {
                remove.reset();
                setMessage("");
                setToDelete(p);
              }}
            />
          ))}
        </ul>
      )}

      {creating ? (
        <NewPortfolioForm
          onCreated={created}
          onCancel={() => {
            setCreating(false);
            requestAnimationFrame(() => newButtonRef.current?.focus());
          }}
        />
      ) : (
        <button
          ref={newButtonRef}
          type="button"
          className={`${buttonPrimary} self-start`}
          onClick={() => {
            setMessage("");
            setCreating(true);
          }}
        >
          Nueva cartera
        </button>
      )}

      <p role="status" className="m-0 text-base text-success empty:hidden">
        {message}
      </p>

      {toDelete && (
        <DeletePortfolioDialog
          portfolio={toDelete}
          last={list.length === 1}
          pending={remove.isPending}
          error={
            remove.isError
              ? "No hemos podido borrar la cartera. Vuelve a intentarlo en unos segundos."
              : ""
          }
          onConfirm={confirmDelete}
          onClose={() => setToDelete(null)}
        />
      )}
    </div>
  );
}
