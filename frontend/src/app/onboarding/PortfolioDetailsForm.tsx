import { useId, useRef, useState, type FormEvent } from "react";
import { buttonPrimary } from "../../components/button";
import { ChoiceGroup } from "./ChoiceGroup";
import {
  KIND_OPTIONS,
  NAME_MAX,
  RISK_OPTIONS,
  validateDetails,
  type DetailsDraft,
  type DetailsErrors,
  type ImportRowError,
  type Method,
} from "./portfolioDetails";

const METHOD_OPTIONS: { value: Method; label: string; hint: string }[] = [
  { value: "manual", label: "Añadirlos uno a uno", hint: "Buscas cada activo por ISIN, ticker o nombre" },
  { value: "csv", label: "Importar un CSV", hint: "Un fichero con una fila por posición" },
];

const INPUT =
  "min-h-touch w-full rounded-control border border-line-strong bg-surface px-3 text-base text-ink aria-invalid:border-error";

interface PortfolioDetailsFormProps {
  pending: boolean;
  /** Mensaje del último fallo al crear o importar ("" si no hay). */
  submitError: string;
  rowErrors: ImportRowError[];
  onSubmit: (draft: DetailsDraft) => void;
}

/**
 * Paso 1 del primer uso: nombre, tipo, perfil de riesgo y cómo añadir los activos. Si falta
 * algo, un resumen recibe el foco y cada campo dice qué le pasa (como en `OnboardingForm`).
 */
export function PortfolioDetailsForm({
  pending,
  submitError,
  rowErrors,
  onSubmit,
}: PortfolioDetailsFormProps) {
  const [draft, setDraft] = useState<DetailsDraft>({
    name: "",
    kind: "personal",
    risk: null,
    method: "manual",
    file: null,
  });
  const [errors, setErrors] = useState<DetailsErrors>({});
  const summaryRef = useRef<HTMLDivElement>(null);
  const id = useId();
  const errorCount = Object.keys(errors).length;
  const set = (patch: Partial<DetailsDraft>) => setDraft((d) => ({ ...d, ...patch }));

  function submit(e: FormEvent) {
    e.preventDefault();
    const found = validateDetails(draft);
    setErrors(found);
    if (Object.keys(found).length > 0) {
      requestAnimationFrame(() => summaryRef.current?.focus());
      return;
    }
    onSubmit({ ...draft, name: draft.name.trim() });
  }

  return (
    <form noValidate onSubmit={submit} className="flex flex-col gap-6">
      {errorCount > 0 && (
        <div
          ref={summaryRef}
          tabIndex={-1}
          role="alert"
          className="rounded-card border border-error bg-error-bg p-4 text-base font-medium text-error"
        >
          {errorCount === 1 ? "Hay 1 campo por revisar." : `Hay ${errorCount} campos por revisar.`}
        </div>
      )}

      <div className="flex flex-col gap-2">
        <label htmlFor={`${id}-name`} className="text-base font-semibold text-ink">
          Nombre de la cartera
        </label>
        <input
          id={`${id}-name`}
          value={draft.name}
          onChange={(e) => set({ name: e.target.value })}
          maxLength={NAME_MAX}
          autoComplete="off"
          aria-invalid={errors.name ? true : undefined}
          aria-describedby={`${id}-name-hint${errors.name ? ` ${id}-name-error` : ""}`}
          className={INPUT}
        />
        <span id={`${id}-name-hint`} className="text-sm text-ink-muted">
          Por ejemplo, «Personal», «Negocio» o «Hijos».
        </span>
        {errors.name && (
          <span id={`${id}-name-error`} className="text-sm font-medium text-error">
            {errors.name}
          </span>
        )}
      </div>

      <ChoiceGroup legend="Tipo" options={KIND_OPTIONS} value={draft.kind} onChange={(kind) => set({ kind })} />
      <ChoiceGroup
        legend="Perfil de riesgo"
        options={RISK_OPTIONS}
        value={draft.risk}
        onChange={(risk) => set({ risk })}
        error={errors.risk}
      />
      <ChoiceGroup
        legend="¿Cómo quieres añadir tus activos?"
        options={METHOD_OPTIONS}
        value={draft.method}
        onChange={(method) => set({ method })}
      />

      {draft.method === "csv" && (
        <div className="flex flex-col gap-2">
          <label htmlFor={`${id}-file`} className="text-base font-semibold text-ink">
            Fichero CSV
          </label>
          <input
            id={`${id}-file`}
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => set({ file: e.target.files?.[0] ?? null })}
            aria-invalid={errors.file ? true : undefined}
            aria-describedby={`${id}-file-hint${errors.file ? ` ${id}-file-error` : ""}`}
            className="text-base text-ink file:mr-3 file:min-h-touch file:cursor-pointer file:rounded-full file:border file:border-line-strong file:bg-surface file:px-5 file:font-semibold file:text-ink"
          />
          <span id={`${id}-file-hint`} className="text-sm text-ink-muted">
            Columnas: <code>asset</code> (ISIN o ticker), <code>units</code>,{" "}
            <code>avg_cost_eur</code> y, si quieres, <code>acquired_at</code> (AAAA-MM-DD).
            Decimales con punto o coma; columnas separadas por coma o punto y coma.
          </span>
          {errors.file && (
            <span id={`${id}-file-error`} className="text-sm font-medium text-error">
              {errors.file}
            </span>
          )}
        </div>
      )}

      <div role="status" className="flex flex-col gap-2 empty:hidden">
        {submitError && <p className="m-0 text-base font-medium text-error">{submitError}</p>}
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
          {pending ? "Creando…" : draft.method === "csv" ? "Importar y crear la cartera" : "Crear la cartera"}
        </button>
      </div>
    </form>
  );
}
