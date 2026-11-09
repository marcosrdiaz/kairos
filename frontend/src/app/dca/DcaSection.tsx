import { useState } from "react";
import { buttonSecondary } from "../../components/button";
import { usePortfolio } from "../operations/usePortfolio";
import { usePortfolioId } from "../portfolio-picker/usePortfolioId";
import { DcaPlanCard } from "./DcaPlanCard";
import { DcaPlanForm } from "./DcaPlanForm";
import { PendingExecutions, type DcaNotice } from "./PendingExecutions";
import { emptyPlan } from "./planDraft";
import { useDcaPlans, usePendingExecutions } from "./useDca";

/** Planes y aportaciones de una cartera. Se monta con `key={portfolioId}` para empezar limpio. */
export function DcaPanel({ portfolioId }: { portfolioId: string }) {
  const portfolio = usePortfolio(portfolioId);
  const plans = useDcaPlans(portfolioId);
  const pending = usePendingExecutions(portfolioId);
  const [creating, setCreating] = useState(false);
  const [notice, setNotice] = useState<DcaNotice | null>(null);

  return (
    <div className="flex flex-col gap-6">
      <p
        role="status"
        className={`m-0 text-base font-semibold empty:hidden ${notice?.tone === "neutral" ? "text-ink" : "text-success"}`}
      >
        {notice?.text ?? ""}
      </p>
      {pending.data && pending.data.length > 0 && (
        <div className="flex flex-col gap-3">
          <h3 className="m-0 text-lg font-semibold text-ink">Pendientes de confirmar</h3>
          <PendingExecutions executions={pending.data} portfolio={portfolio.data} onResolved={setNotice} />
        </div>
      )}
      {pending.isError && (
        <p className="m-0 text-base text-ink-muted">
          Ahora mismo no podemos comprobar si hay aportaciones pendientes.
        </p>
      )}
      <div className="flex flex-col gap-3">
        <h3 className="m-0 text-lg font-semibold text-ink">Planes</h3>
        {plans.isPending && (
          <div
            aria-hidden="true"
            className="h-32 animate-pulse rounded-card bg-surface-muted motion-reduce:animate-none"
          />
        )}
        {plans.isError && (
          <p className="m-0 text-base text-ink-muted">
            Ahora mismo no podemos cargar los planes. Vuelve a intentarlo en unos segundos.
          </p>
        )}
        {plans.data?.length === 0 && !creating && (
          <p className="m-0 text-base text-ink-muted">Esta cartera aún no tiene ningún plan de aportaciones.</p>
        )}
        {plans.data?.map((plan) => (
          <DcaPlanCard
            key={plan.id}
            plan={plan}
            portfolioId={portfolioId}
            portfolio={portfolio.data}
            onUpdated={() => setNotice({ tone: "success", text: "Plan de aportaciones actualizado." })}
          />
        ))}
        {creating ? (
          <DcaPlanForm
            portfolioId={portfolioId}
            initial={emptyPlan()}
            onDone={() => {
              setCreating(false);
              setNotice({ tone: "success", text: "Plan de aportaciones creado." });
            }}
            onCancel={() => setCreating(false)}
          />
        ) : (
          <button
            type="button"
            className={`${buttonSecondary} self-start`}
            onClick={() => {
              setNotice(null);
              setCreating(true);
            }}
          >
            Crear un plan de aportaciones
          </button>
        )}
      </div>
    </div>
  );
}

/** Bloque "Aportaciones periódicas" de Cartera (RF-07), sobre la cartera elegida en `?p=`. */
export function DcaSection() {
  const [portfolioId] = usePortfolioId();
  return (
    <section aria-labelledby="dca-title" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 id="dca-title" className="m-0 text-xl font-semibold text-ink">
          Aportaciones periódicas
        </h2>
        <p className="m-0 text-base text-ink-muted">
          Tu plan de aportar una cantidad fija cada mes o cada semana. Cuando toca, Kairos te pide
          confirmarla y la apunta en la cartera; no mueve dinero ni envía órdenes.
        </p>
      </div>
      <DcaPanel key={portfolioId} portfolioId={portfolioId} />
    </section>
  );
}
