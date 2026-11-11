import { useEffect, useRef, useState } from "react";
import { useCreatePortfolio } from "../../api/hooks/usePortfolioCreate";
import type { PortfolioCreateRequest, PortfolioSummaryOut } from "../../api/generated/schema";
import { buttonSecondary } from "../../components/button";
import { AddAssetsStep } from "../onboarding/AddAssetsStep";
import { PortfolioDetailsForm } from "../onboarding/PortfolioDetailsForm";
import { createErrorText, type DetailsDraft } from "../onboarding/portfolioDetails";

interface NewPortfolioFormProps {
  /** Al terminar: la cartera creada (vacía o con posiciones), o la importada desde un CSV. */
  onCreated: (portfolio: PortfolioSummaryOut, imported: boolean) => void;
  onCancel: () => void;
}

/**
 * «Nueva cartera» en Cartera (T4-13), en los mismos dos pasos que el asistente de primer uso:
 * 1. `PortfolioDetailsForm` crea la cartera vacía. 2. `AddAssetsStep`: posiciones a mano o
 * importar un CSV; «Terminar» la deja elegida. Cancelar solo se ofrece en el paso 1 (en el 2 la
 * cartera ya existe). Al abrirse y al pasar de paso, el foco va al titular.
 */
export function NewPortfolioForm({ onCreated, onCancel }: NewPortfolioFormProps) {
  const create = useCreatePortfolio();
  const [created, setCreated] = useState<{ portfolio: PortfolioSummaryOut; details: PortfolioCreateRequest } | null>(
    null,
  );
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    headingRef.current?.focus();
  }, [created]);

  function submit(draft: DetailsDraft) {
    create.reset();
    if (!draft.risk) return; // validateDetails ya lo exige: solo estrecha el tipo
    const details = { name: draft.name, kind: draft.kind, risk_profile: draft.risk };
    create.mutate(details, { onSuccess: (portfolio) => setCreated({ portfolio, details }) });
  }

  return (
    <section
      aria-labelledby="new-portfolio-title"
      className="flex flex-col gap-6 border-t border-line pt-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <p className="m-0 text-sm font-medium text-ink-muted">{created ? "Paso 2 de 2" : "Paso 1 de 2"}</p>
          <h3
            id="new-portfolio-title"
            ref={headingRef}
            tabIndex={-1}
            className="m-0 text-lg font-semibold text-ink outline-none"
          >
            {created ? `Añade los activos de «${created.portfolio.name}»` : "Nueva cartera"}
          </h3>
        </div>
        {!created && (
          <button type="button" className={buttonSecondary} onClick={onCancel}>
            Cancelar
          </button>
        )}
      </div>
      {created ? (
        <AddAssetsStep
          portfolio={created.portfolio}
          details={created.details}
          finishLabel="Terminar"
          requireAssets={false}
          onFinish={onCreated}
        />
      ) : (
        <PortfolioDetailsForm
          pending={create.isPending}
          submitError={create.error ? createErrorText(create.error) : ""}
          onSubmit={submit}
        />
      )}
    </section>
  );
}
