import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiPatch } from "../../api/client";
import type { DcaPlanOut, DcaPlanStatus, PortfolioOut } from "../../api/generated/schema";
import { buttonSecondary } from "../../components/button";
import { formatDate, formatEur, formatPercent } from "../../lib/format";
import { assetName } from "../operations/usePortfolio";
import { DcaPlanForm } from "./DcaPlanForm";
import { draftFromPlan } from "./planDraft";

const WEEK_DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábados", "domingos"];

function schedule(plan: DcaPlanOut): string {
  return plan.frequency === "monthly"
    ? `cada mes, el día ${plan.day}`
    : `cada semana, los ${WEEK_DAYS[plan.day - 1] ?? `día ${plan.day}`}`;
}

interface DcaPlanCardProps {
  plan: DcaPlanOut;
  portfolioId: string;
  portfolio: PortfolioOut | undefined;
  /** Tras guardar la edición, para anunciarlo en el bloque. */
  onUpdated: () => void;
}

/** Un plan de aportaciones: qué, cuándo y a qué activos; pausar, reanudar o editar (RF-07). */
export function DcaPlanCard({ plan, portfolioId, portfolio, onUpdated }: DcaPlanCardProps) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const paused = plan.status === "paused";

  const setStatus = useMutation({
    mutationFn: (status: DcaPlanStatus) =>
      apiPatch<DcaPlanOut>(
        `/portfolios/${encodeURIComponent(portfolioId)}/dca-plans/${encodeURIComponent(plan.id)}`,
        { status },
        { mock: "DcaPlanOut" },
      ),
    onSuccess: () => void queryClient.invalidateQueries(),
  });

  if (editing) {
    return (
      <DcaPlanForm
        portfolioId={portfolioId}
        plan={plan}
        initial={draftFromPlan(plan, portfolio)}
        onDone={() => {
          setEditing(false);
          onUpdated();
        }}
        onCancel={() => setEditing(false)}
      />
    );
  }

  return (
    <article
      aria-label={`Plan de ${formatEur(plan.amount_eur)} ${schedule(plan)}`}
      className="flex flex-col gap-4 rounded-card border border-line bg-surface p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="m-0 text-lg font-semibold text-ink">
          <span className="tabular-nums">{formatEur(plan.amount_eur)}</span> {schedule(plan)}
        </p>
        <span
          className={`rounded-full px-3 py-1 text-base font-semibold ${paused ? "bg-nodata-bg text-nodata" : "bg-success-bg text-success"}`}
        >
          {paused ? "En pausa" : "Activo"}
        </span>
      </div>
      <ul className="m-0 flex list-none flex-col gap-1 p-0" aria-label="Reparto">
        {plan.allocations.map((a) => (
          <li key={a.asset_id} className="flex flex-wrap justify-between gap-2 text-ink">
            <span>{assetName(portfolio, a.asset_id)}</span>
            <span className="tabular-nums">{formatPercent(a.weight)}</span>
          </li>
        ))}
      </ul>
      {!paused && plan.next_execution_at && (
        <p className="m-0 text-base text-ink-muted">Próxima aportación: {formatDate(plan.next_execution_at)}</p>
      )}
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className={buttonSecondary}
          disabled={setStatus.isPending}
          aria-disabled={setStatus.isPending}
          onClick={() => setStatus.mutate(paused ? "active" : "paused")}
        >
          {paused ? "Reanudar plan" : "Pausar plan"}
        </button>
        <button type="button" className={buttonSecondary} onClick={() => setEditing(true)}>
          Editar plan
        </button>
      </div>
      <p role="status" className="m-0 text-base font-medium text-error empty:hidden">
        {setStatus.isError ? "No hemos podido cambiar el estado del plan. Vuelve a intentarlo." : ""}
      </p>
    </article>
  );
}
