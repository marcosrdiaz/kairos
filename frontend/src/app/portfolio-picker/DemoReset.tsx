import { useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiPost } from "../../api/client";
import type { DemoResetOut, DemoResetRequest } from "../../api/generated/schema";
import { buttonPrimary, buttonSecondary } from "../../components/button";

/** El guion precarga BCE y petróleo (DemoResetRequest.preload). */
const RESET_BODY: DemoResetRequest = { preload: true };

function errorText(error: unknown): string {
  if (error instanceof ApiError && error.code === "DEMO_MODE_DISABLED") {
    return "Restaurar las carteras de ejemplo solo está disponible en el modo demo.";
  }
  return "No hemos podido restaurar las carteras. Vuelve a intentarlo en unos segundos.";
}

/**
 * "Cargar cartera de ejemplo" (RF-02): `POST /demo/reset` deja Carmen, Javier y Víctor en su estado
 * inicial. Borra las operaciones hechas, así que pide confirmación en el sitio (sin modal) y
 * pone el foco en "Cancelar", la opción que no destruye nada. Al terminar, recarga todos los datos.
 */
export function DemoReset() {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const reset = useMutation({
    mutationFn: () =>
      apiPost<DemoResetOut>("/demo/reset", RESET_BODY, { mock: "DemoResetOut" }),
    onSuccess: () => {
      setConfirming(false);
      void queryClient.invalidateQueries();
    },
  });

  useEffect(() => {
    if (confirming) cancelRef.current?.focus();
  }, [confirming]);

  return (
    <div className="flex flex-col gap-3">
      {confirming ? (
        <div
          role="group"
          aria-labelledby="demo-reset-question"
          className="flex flex-col gap-3 rounded-card border border-line-strong bg-surface-muted p-4"
        >
          <p id="demo-reset-question" className="m-0 text-base text-ink">
            Se borrarán las posiciones y operaciones que hayas añadido y las carteras de ejemplo
            volverán a su estado inicial.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className={buttonPrimary}
              disabled={reset.isPending}
              aria-disabled={reset.isPending}
              onClick={() => reset.mutate()}
            >
              {reset.isPending ? "Restaurando…" : "Sí, restaurar"}
            </button>
            <button
              ref={cancelRef}
              type="button"
              className={buttonSecondary}
              disabled={reset.isPending}
              onClick={() => setConfirming(false)}
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          className={`${buttonSecondary} self-start`}
          onClick={() => {
            reset.reset();
            setConfirming(true);
          }}
        >
          Cargar carteras de ejemplo
        </button>
      )}
      <p role="status" className="m-0 text-base empty:hidden">
        {reset.isSuccess && (
          <span className="text-success">Carmen, Javier y Víctor vuelven a estar en su estado inicial.</span>
        )}
        {reset.isError && <span className="text-error">{errorText(reset.error)}</span>}
      </p>
    </div>
  );
}
