import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiPost } from "../../api/client";
import type { DcaExecutionActionRequest, DcaExecutionOut, PortfolioOut } from "../../api/generated/schema";
import { buttonPrimary, buttonSecondary } from "../../components/button";
import { formatDate, formatEur, formatUnits } from "../../lib/format";
import { assetName, findPosition, formatPrice } from "../operations/usePortfolio";

type Action = DcaExecutionActionRequest["action"];

function actionErrorText(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 422) return "Esta aportación ya estaba confirmada o saltada.";
    if (error.code === "PRICE_UNAVAILABLE") {
      return "Ahora mismo no hay precio para registrar la compra. No se ha registrado nada.";
    }
  }
  return "No hemos podido guardar la respuesta. Vuelve a intentarlo en unos segundos.";
}

interface ExecutionProps {
  execution: DcaExecutionOut;
  portfolio: PortfolioOut | undefined;
  onResolved: (text: string) => void;
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
      onResolved(
        action === "confirm"
          ? `Aportación del ${formatDate(done.scheduled_for)} confirmada y registrada en la cartera al precio del momento.`
          : `Aportación del ${formatDate(done.scheduled_for)} saltada. El plan sigue igual.`,
      );
      void queryClient.invalidateQueries();
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 422) void queryClient.invalidateQueries();
    },
  });
  const date = formatDate(execution.scheduled_for);

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
          disabled={act.isPending}
          aria-disabled={act.isPending}
          onClick={() => act.mutate("confirm")}
        >
          {act.isPending && act.variables === "confirm" ? "Confirmando…" : "Confirmar aportación"}
        </button>
        <button
          type="button"
          className={buttonSecondary}
          disabled={act.isPending}
          aria-disabled={act.isPending}
          onClick={() => act.mutate("skip")}
        >
          Saltar esta vez
        </button>
      </div>
      <p role="status" className="m-0 text-base font-medium text-error empty:hidden">
        {act.isError ? actionErrorText(act.error) : ""}
      </p>
    </li>
  );
}

interface PendingExecutionsProps {
  executions: DcaExecutionOut[];
  portfolio: PortfolioOut | undefined;
  onResolved: (text: string) => void;
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
