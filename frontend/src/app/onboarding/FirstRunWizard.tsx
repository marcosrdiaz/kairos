import { useEffect, useRef, useState } from "react";
import { useCreatePortfolio, useImportPortfolio } from "../../api/hooks/usePortfolioCreate";
import type { PortfolioSummaryOut } from "../../api/generated/schema";
import { buttonPrimary, buttonDisabled } from "../../components/button";
import { OnboardingForm } from "./OnboardingForm";
import { PortfolioDetailsForm } from "./PortfolioDetailsForm";
import {
  CSV_MAX_CHARS,
  createErrorText,
  importRowErrors,
  type DetailsDraft,
} from "./portfolioDetails";

interface FirstRunWizardProps {
  /** Al terminar: la cartera creada, para elegirla y abrir Inicio. */
  onDone: (portfolioId: string) => void;
}

/**
 * Asistente de primer uso (T4-12): sin ninguna cartera, se crea la primera.
 * 1. Nombre, tipo, perfil y método. Con CSV, la importación crea la cartera con sus posiciones
 *    y se termina. A mano, se crea vacía y se pasa al paso 2.
 * 2. Alta de posiciones con `OnboardingForm`; «Ir a Inicio» se activa con la primera guardada.
 * Cada paso lleva el foco a su titular para que el lector anuncie el cambio.
 */
export function FirstRunWizard({ onDone }: FirstRunWizardProps) {
  const create = useCreatePortfolio();
  const importer = useImportPortfolio();
  const [created, setCreated] = useState<PortfolioSummaryOut | null>(null);
  const [saved, setSaved] = useState(false);
  const [fileError, setFileError] = useState("");
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (created) headingRef.current?.focus();
  }, [created]);

  async function submit(draft: DetailsDraft) {
    setFileError("");
    create.reset();
    importer.reset();
    // validateDetails ya exige el perfil: esto solo estrecha el tipo.
    if (!draft.risk) return;
    const base = { name: draft.name, kind: draft.kind, risk_profile: draft.risk };
    if (draft.method === "manual") {
      create.mutate(base, { onSuccess: (p) => setCreated(p) });
      return;
    }
    if (!draft.file) return;
    const csv = await draft.file.text();
    if (!csv.trim()) {
      setFileError("El fichero está vacío.");
      return;
    }
    if (csv.length > CSV_MAX_CHARS) {
      setFileError("El fichero es demasiado grande. Divide las posiciones en varios ficheros.");
      return;
    }
    importer.mutate(
      { ...base, csv, dry_run: false },
      { onSuccess: (out) => out.portfolio && onDone(out.portfolio.id) },
    );
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
            Añade los activos de «{created.name}»
          </h1>
          <p className="m-0 text-base text-ink-muted">
            Busca cada fondo, ETF o acción por su ISIN, ticker o nombre. Del resto (tipo, divisa,
            clase, comisión y si es traspasable) nos encargamos nosotros.
          </p>
        </div>
        <OnboardingForm portfolioId={created.id} onSaved={() => setSaved(true)} />
        <div className="flex flex-col gap-2 border-t border-line pt-6">
          <button
            type="button"
            className={saved ? buttonPrimary : buttonDisabled}
            aria-disabled={!saved}
            aria-describedby={saved ? undefined : "first-run-done-hint"}
            onClick={() => saved && onDone(created.id)}
          >
            Ir a Inicio
          </button>
          {!saved && (
            <span id="first-run-done-hint" className="text-sm text-ink-muted">
              Guarda al menos una posición para ver tu cartera.
            </span>
          )}
        </div>
      </section>
    );
  }

  const error = create.error ?? importer.error;
  return (
    <section aria-labelledby="first-run-step1" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <p className="m-0 text-sm font-medium text-ink-muted">Paso 1 de 2</p>
        <h1 id="first-run-step1" className="m-0 text-2xl font-semibold leading-tight text-ink">
          Crea tu primera cartera
        </h1>
        <p className="m-0 text-base text-ink-muted">
          Kairos te explica cómo te afectan las noticias según lo que tienes. Empieza por decirnos
          qué cartera es y qué hay en ella. Podrás crear más carteras después; cada una va por
          separado.
        </p>
      </div>
      <PortfolioDetailsForm
        pending={create.isPending || importer.isPending}
        submitError={fileError || (error ? createErrorText(error) : "")}
        rowErrors={importRowErrors(importer.error)}
        onSubmit={(d) => void submit(d)}
      />
    </section>
  );
}
