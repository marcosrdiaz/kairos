import { useEffect, useRef, useState } from "react";
import { useCreatePortfolio, useImportPortfolio } from "../../api/hooks/usePortfolioCreate";
import type { PortfolioSummaryOut } from "../../api/generated/schema";
import { buttonSecondary } from "../../components/button";
import { PortfolioDetailsForm } from "../onboarding/PortfolioDetailsForm";
import {
  CSV_MAX_CHARS,
  createErrorText,
  importRowErrors,
  type DetailsDraft,
} from "../onboarding/portfolioDetails";

interface NewPortfolioFormProps {
  /** La cartera creada (vacía, o con sus posiciones si venía de un CSV). */
  onCreated: (portfolio: PortfolioSummaryOut, imported: boolean) => void;
  onCancel: () => void;
}

/**
 * «Nueva cartera» en Cartera (T4-13): el mismo paso 1 del asistente de primer uso
 * (`PortfolioDetailsForm`). A mano, crea la cartera vacía; las posiciones se añaden después en
 * «Añadir posiciones». Con CSV, la importa con sus posiciones. Al abrirse, el foco va al titular.
 */
export function NewPortfolioForm({ onCreated, onCancel }: NewPortfolioFormProps) {
  const create = useCreatePortfolio();
  const importer = useImportPortfolio();
  const [fileError, setFileError] = useState("");
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    headingRef.current?.focus();
  }, []);

  async function submit(draft: DetailsDraft) {
    setFileError("");
    create.reset();
    importer.reset();
    if (!draft.risk) return; // validateDetails ya lo exige: solo estrecha el tipo
    const base = { name: draft.name, kind: draft.kind, risk_profile: draft.risk };
    if (draft.method === "manual") {
      create.mutate(base, { onSuccess: (p) => onCreated(p, false) });
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
      { onSuccess: (out) => out.portfolio && onCreated(out.portfolio, true) },
    );
  }

  const error = create.error ?? importer.error;
  return (
    <section
      aria-labelledby="new-portfolio-title"
      className="flex flex-col gap-6 rounded-card border border-line bg-surface p-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3
          id="new-portfolio-title"
          ref={headingRef}
          tabIndex={-1}
          className="m-0 text-lg font-semibold text-ink outline-none"
        >
          Nueva cartera
        </h3>
        <button type="button" className={buttonSecondary} onClick={onCancel}>
          Cancelar
        </button>
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
