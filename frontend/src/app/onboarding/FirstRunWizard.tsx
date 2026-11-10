import { useEffect, useRef, useState } from "react";
import { useCreatePortfolio } from "../../api/hooks/usePortfolioCreate";
import type { PortfolioCreateRequest, PortfolioSummaryOut } from "../../api/generated/schema";
import { AddAssetsStep } from "./AddAssetsStep";
import { PortfolioDetailsForm } from "./PortfolioDetailsForm";
import { createErrorText, type DetailsDraft } from "./portfolioDetails";

interface FirstRunWizardProps {
  /** Al terminar: la cartera creada, para elegirla y abrir Inicio. */
  onDone: (portfolioId: string) => void;
}

/**
 * Asistente de primer uso (T4-12): sin ninguna cartera, se crea la primera.
 * 1. Nombre, tipo y perfil: «Continuar» crea la cartera vacía.
 * 2. `AddAssetsStep`: posiciones a mano o «Importar un CSV» (que sustituye a la vacía).
 *    «Ir a Inicio» se activa al guardar o importar.
 * Cada paso lleva el foco a su titular para que el lector anuncie el cambio.
 */
export function FirstRunWizard({ onDone }: FirstRunWizardProps) {
  const create = useCreatePortfolio();
  const [created, setCreated] = useState<{ portfolio: PortfolioSummaryOut; details: PortfolioCreateRequest } | null>(
    null,
  );
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (created) headingRef.current?.focus();
  }, [created]);

  function submit(draft: DetailsDraft) {
    create.reset();
    // validateDetails ya exige el perfil: esto solo estrecha el tipo.
    if (!draft.risk) return;
    const details = { name: draft.name, kind: draft.kind, risk_profile: draft.risk };
    create.mutate(details, { onSuccess: (portfolio) => setCreated({ portfolio, details }) });
  }

  if (created) {
    return (
      <section aria-labelledby="first-run-step2" className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <p className="m-0 text-sm font-medium text-ink-muted">Paso 2 de 2</p>
          <h1
            id="first-run-step2"
            ref={headingRef}
            tabIndex={-1}
            className="m-0 text-2xl font-semibold leading-tight text-ink outline-none"
          >
            Añade los activos de «{created.portfolio.name}»
          </h1>
          <p className="m-0 text-base text-ink-muted">
            Busca cada fondo, ETF o acción por su ISIN, ticker o nombre y di cuántas participaciones
            tienes. Del resto (precio, tipo, divisa, clase, comisión y si es traspasable) nos
            encargamos nosotros.
          </p>
        </div>
        <AddAssetsStep
          portfolio={created.portfolio}
          details={created.details}
          finishLabel="Ir a Inicio"
          requireAssets
          onFinish={(p) => onDone(p.id)}
        />
      </section>
    );
  }

  return (
    <section aria-labelledby="first-run-step1" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <p className="m-0 text-sm font-medium text-ink-muted">Paso 1 de 2</p>
        <h1 id="first-run-step1" className="m-0 text-2xl font-semibold leading-tight text-ink">
          Crea tu primera cartera
        </h1>
        <p className="m-0 text-base text-ink-muted">
          Kairos te explica cómo te afectan las noticias según lo que tienes. Empieza por decirnos
          qué cartera es; en el siguiente paso añadirás sus activos. Podrás crear más carteras
          después; cada una va por separado.
        </p>
      </div>
      <PortfolioDetailsForm
        pending={create.isPending}
        submitError={create.error ? createErrorText(create.error) : ""}
        onSubmit={submit}
      />
    </section>
  );
}
