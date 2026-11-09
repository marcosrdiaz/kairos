import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiPost } from "../../api/client";
import type { DcaExecutionActionRequest, DcaExecutionOut, PortfolioOut } from "../../api/generated/schema";
import { buttonPrimary, buttonSecondary } from "../../components/button";
import { formatDate, formatEur, formatUnits } from "../../lib/format";
import { assetName, findPosition, formatPrice } from "../operations/usePortfolio";

type Action = DcaExecutionActionRequest["action"];

/** Aviso del bloque de aportaciones: sobrevive a que la aportación salga de la lista. */
export interface DcaNotice {
  text: string;
  tone: "success" | "neutral";
}

/**
 * 422 de «ya confirmada o saltada» (`portfolio/errors.py`, `dca_execution_resolved`): lo dicen
 * `details.execution_id` y `details.status`. Otro 422 (p. ej. de validación) es un error normal.
 */
const alreadyResolved = (error: unknown, executionId: string) =>
  error instanceof ApiError &&
  error.status === 422 &&
  error.details.execution_id === executionId &&
  (error.details.status === "confirmed" || error.details.status === "skipped");

function actionErrorText(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "PRICE_UNAVAILABLE") {
      return "Ahora mismo no hay precio para registrar la compra. No se ha registrado nada.";
    }
  }
  return "No hemos podido guardar la respuesta. Vuelve a intentarlo en unos segundos.";
}

interface ExecutionProps {
  execution: DcaExecutionOut;
  portfolio: PortfolioOut | undefined;
  onResolved: (notice: DcaNotice) => void;
}

function PendingExecution({ execution, portfolio, onResolved }: ExecutionProps) {
  const queryClient = useQueryClient();
  const act = useMutation({
    mutationFn: (action: Action) =>
      apiPost<DcaExecutionOut>(
        `/dca-executions/${encodeURIComponent(execution.id)}`,
        { action },
        { mock: "DcaExecutionOut" },
      ),
    onSuccess: (done, action) => {
      onResolved({
        tone: "success",
        text:
          action === "confirm"
            ? `Aportación del ${formatDate(done.scheduled_for)} confirmada y registrada en la cartera al precio del momento.`
            : `Aportación del ${formatDate(done.scheduled_for)} saltada. El plan sigue igual.`,
      });
      void queryClient.invalidateQueries();
    },
    onError: (error) => {
      // Ya resuelta (p. ej. en otra pestaña): al recargar sale de la lista, así que el aviso
      // va al bloque y no a esta tarjeta.
      if (!alreadyResolved(error, execution.id)) return;
      onResolved({
        tone: "neutral",
        text: `La aportación del ${formatDate(execution.scheduled_for)} ya estaba confirmada o saltada. No se ha cambiado nada.`,
      });
      void queryClient.invalidateQueries();
    },
  });
  const date = formatDate(execution.scheduled_for);
  // Tras resolverla, la tarjeta sigue hasta que llega la lista nueva: sin segundo clic.
  const locked = act.isPending || act.isSuccess;

  return (
    <li className="flex flex-col gap-4 rounded-card border border-line bg-surface p-5">
      <h4 className="m-0 text-lg font-semibold text-ink">Aportación del {date}</h4>
      <ul className="m-0 flex list-none flex-col gap-3 p-0">
        {execution.lines.map((line) => {
          const currency = findPosition(portfolio, line.asset_id)?.price_currency;
          return (
            <li key={line.asset_id} className="flex flex-col gap-1">
              <span className="font-semibold text-ink">{assetName(portfolio, line.asset_id)}</span>
              <span className="text-ink tabular-nums">
                {formatEur(line.amount_eur)} · unas {formatUnits(line.units_estimated)} participaciones a{" "}
                {formatPrice(line.price, currency)}{" "}
                <span className="text-ink-muted">(precio del {formatDate(line.price_at)})</span>
              </span>
            </li>
          );
        })}
      </ul>
      <p className="m-0 text-base text-ink-muted">
        Al confirmar se registra la compra al precio de ese momento, así que las participaciones
        pueden variar un poco respecto a las estimadas.
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className={buttonPrimary}
          disabled={locked}
          aria-disabled={locked}
          onClick={() => act.mutate("confirm")}
        >
          {act.isPending && act.variables === "confirm" ? "Confirmando…" : "Confirmar aportación"}
        </button>
        <button
          type="button"
          className={buttonSecondary}
          disabled={locked}
          aria-disabled={locked}
          onClick={() => act.mutate("skip")}
        >
          Saltar esta vez
        </button>
      </div>
      <p role="status" className="m-0 text-base font-medium text-error empty:hidden">
        {act.isError && !alreadyResolved(act.error, execution.id) ? actionErrorText(act.error) : ""}
      </p>
    </li>
  );
}

interface PendingExecutionsProps {
  executions: DcaExecutionOut[];
  portfolio: PortfolioOut | undefined;
  onResolved: (notice: DcaNotice) => void;
}

/** Aportaciones pendientes de confirmar o saltar (UC-12). Confirmar crea un `dca_buy`. */
export function PendingExecutions({ executions, portfolio, onResolved }: PendingExecutionsProps) {
  return (
    <ul className="m-0 flex list-none flex-col gap-4 p-0" aria-label="Aportaciones pendientes">
      {executions.map((x) => (
        <PendingExecution key={x.id} execution={x} portfolio={portfolio} onResolved={onResolved} />
      ))}
    </ul>
  );
}
