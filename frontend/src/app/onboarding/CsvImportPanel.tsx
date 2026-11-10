import { useId, useRef, useState, type FormEvent } from "react";
import { useImportPortfolio } from "../../api/hooks/usePortfolioCreate";
import { useDeletePortfolio } from "../../api/hooks/usePortfolioManage";
import type { PortfolioCreateRequest, PortfolioSummaryOut } from "../../api/generated/schema";
import { buttonPrimary, buttonSecondary } from "../../components/button";
import { createErrorText, importRowErrors, readCsvFile } from "./portfolioDetails";

export interface ImportDone {
  /** La cartera importada, que sustituye a la vacía del paso 1. */
  portfolio: PortfolioSummaryOut;
  /** Filas del CSV guardadas (lo que devuelve el backend). */
  count: number;
  /** Si no se pudo borrar la cartera vacía (queda en la lista y se puede borrar en Cartera). */
  emptyLeft: boolean;
}

interface CsvImportPanelProps {
  /** La cartera vacía creada en el paso 1. */
  empty: PortfolioSummaryOut;
  /** Nombre, tipo y perfil elegidos en el paso 1 (la importada se crea igual). */
  details: PortfolioCreateRequest;
  onImported: (done: ImportDone) => void;
}

/**
 * «Importar un CSV» en el paso 2. El contrato no importa en una cartera existente, así que se
 * crea una cartera nueva con el CSV y los mismos datos del paso 1 (`POST /portfolios/import`) y,
 * si va bien, se borra la vacía (`DELETE /portfolios/{id}`). Si alguna fila falla, el backend
 * no crea nada y se lista cada fila con su error.
 */
export function CsvImportPanel({ empty, details, onImported }: CsvImportPanelProps) {
  const importer = useImportPortfolio();
  const remove = useDeletePortfolio();
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const id = useId();
  const pending = importer.isPending || remove.isPending;
  const rowErrors = importRowErrors(importer.error);
  const message = fileError || (importer.error ? createErrorText(importer.error) : "");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setFileError("");
    importer.reset();
    const read = await readCsvFile(file);
    if (!read.ok) {
      setFileError(read.error);
      fileRef.current?.focus();
      return;
    }
    importer.mutate(
      { ...details, csv: read.csv, dry_run: false },
      {
        onSuccess: (out) => {
          const created = out.portfolio;
          if (!created) return;
          const count = out.positions.length;
          remove.mutate(empty.id, {
            onSuccess: () => onImported({ portfolio: created, count, emptyLeft: false }),
            onError: () => onImported({ portfolio: created, count, emptyLeft: true }),
          });
        },
      },
    );
  }

  return (
    <div className="flex flex-col gap-4 border-t border-line pt-6">
      <div className="flex flex-col gap-2">
        <p className="m-0 text-base text-ink-muted">¿Tienes tus posiciones en una hoja de cálculo?</p>
        <button
          type="button"
          className={`${buttonSecondary} self-start`}
          aria-expanded={open}
          aria-controls={`${id}-panel`}
          onClick={() => {
            setOpen(!open);
            if (!open) requestAnimationFrame(() => fileRef.current?.focus());
          }}
        >
          Importar un CSV
        </button>
      </div>
      {open && (
        <form id={`${id}-panel`} noValidate onSubmit={(e) => void submit(e)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label htmlFor={`${id}-file`} className="text-base font-semibold text-ink">
              Fichero CSV
            </label>
            <input
              ref={fileRef}
              id={`${id}-file`}
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setFileError("");
              }}
              aria-invalid={fileError ? true : undefined}
              aria-describedby={`${id}-file-hint${fileError ? ` ${id}-file-error` : ""}`}
              className="text-base text-ink file:mr-3 file:min-h-touch file:cursor-pointer file:rounded-full file:border file:border-line-strong file:bg-surface file:px-5 file:font-semibold file:text-ink"
            />
            <span id={`${id}-file-hint`} className="text-sm text-ink-muted">
              Columnas: <code>asset</code> (ISIN o ticker), <code>units</code>,{" "}
              <code>avg_cost_eur</code> y, si quieres, <code>acquired_at</code> (AAAA-MM-DD).
              Decimales con punto o coma; columnas separadas por coma o punto y coma.
            </span>
            {fileError && (
              <span id={`${id}-file-error`} className="text-sm font-medium text-error">
                {fileError}
              </span>
            )}
          </div>
          <div role="status" className="flex flex-col gap-2 empty:hidden">
            {message && !fileError && <p className="m-0 text-base font-medium text-error">{message}</p>}
            {rowErrors.length > 0 && (
              <ul className="m-0 flex flex-col gap-1 pl-5 text-base text-error">
                {rowErrors.map((r, i) => (
                  <li key={`${r.line}-${r.field ?? ""}-${i}`}>
                    Línea {r.line}
                    {r.field ? ` (${r.field})` : ""}: {r.message}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <button type="submit" className={buttonPrimary} disabled={pending} aria-disabled={pending}>
              {pending ? "Importando…" : "Importar"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
