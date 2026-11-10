import { useEffect, useRef, useState } from "react";
import type { PortfolioCreateRequest, PortfolioSummaryOut } from "../../api/generated/schema";
import { buttonDisabled, buttonPrimary } from "../../components/button";
import { CsvImportPanel, type ImportDone } from "./CsvImportPanel";
import { OnboardingForm } from "./OnboardingForm";

interface AddAssetsStepProps {
  /** La cartera vacía creada en el paso 1. */
  portfolio: PortfolioSummaryOut;
  /** Nombre, tipo y perfil del paso 1 (para crear la importada igual). */
  details: PortfolioCreateRequest;
  /** Texto del botón final («Ir a Inicio», «Terminar»). */
  finishLabel: string;
  /** Si el botón final espera a que haya posiciones (primer uso). */
  requireAssets: boolean;
  /** La cartera con la que se termina (la importada sustituye a la vacía). */
  onFinish: (portfolio: PortfolioSummaryOut, imported: boolean) => void;
}

/**
 * Paso 2 de crear una cartera, compartido por el asistente de primer uso y «Nueva cartera»:
 * alta de posiciones a mano (`OnboardingForm`) o «Importar un CSV». El import sustituye a la
 * cartera vacía, así que solo se ofrece mientras no se haya guardado nada a mano.
 */
export function AddAssetsStep({ portfolio, details, finishLabel, requireAssets, onFinish }: AddAssetsStepProps) {
  const [saved, setSaved] = useState(false);
  const [imported, setImported] = useState<ImportDone | null>(null);
  const importedRef = useRef<HTMLDivElement>(null);
  const ready = !requireAssets || saved || imported !== null;
  const hintId = `add-assets-done-hint-${portfolio.id}`;

  useEffect(() => {
    if (imported) importedRef.current?.focus();
  }, [imported]);

  function finish() {
    if (!ready) return;
    if (imported) onFinish(imported.portfolio, true);
    else onFinish(portfolio, false);
  }

  return (
    <div className="flex flex-col gap-6">
      {imported ? (
        <div
          ref={importedRef}
          tabIndex={-1}
          role="status"
          className="flex flex-col gap-1 rounded-card border border-line bg-surface-muted p-5 outline-none"
        >
          <p className="m-0 text-lg font-semibold text-success">
            {imported.count === 1
              ? `Hemos importado 1 posición en «${imported.portfolio.name}».`
              : `Hemos importado ${imported.count} posiciones en «${imported.portfolio.name}».`}
          </p>
          {imported.emptyLeft && (
            <p className="m-0 text-base text-ink-muted">
              No hemos podido borrar la cartera vacía que se creó antes. Puedes borrarla en Cartera.
            </p>
          )}
        </div>
      ) : (
        <>
          <OnboardingForm portfolioId={portfolio.id} onSaved={() => setSaved(true)} />
          {!saved && (
            <CsvImportPanel empty={portfolio} details={details} onImported={setImported} />
          )}
        </>
      )}
      <div className="flex flex-col gap-2 border-t border-line pt-6">
        <button
          type="button"
          className={`${ready ? buttonPrimary : buttonDisabled} self-start`}
          aria-disabled={!ready}
          aria-describedby={ready ? undefined : hintId}
          onClick={finish}
        >
          {finishLabel}
        </button>
        {!ready && (
          <span id={hintId} className="text-sm text-ink-muted">
            Guarda al menos una posición o importa un CSV para ver tu cartera.
          </span>
        )}
      </div>
    </div>
  );
}
