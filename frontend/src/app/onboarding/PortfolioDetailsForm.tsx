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
} from "./portfolioDetails";

const INPUT =
  "min-h-touch w-full rounded-control border border-line-strong bg-surface px-3 text-base text-ink aria-invalid:border-error";

interface PortfolioDetailsFormProps {
  pending: boolean;
  /** Mensaje del último fallo al crear ("" si no hay). */
  submitError: string;
  onSubmit: (draft: DetailsDraft) => void;
}

/**
 * Paso 1 de crear una cartera: nombre, tipo y perfil de riesgo. Los activos se añaden en el
 * paso 2 (`AddAssetsStep`). Si falta algo, un resumen recibe el foco y cada campo dice qué le
 * pasa (como en `OnboardingForm`).
 */
export function PortfolioDetailsForm({ pending, submitError, onSubmit }: PortfolioDetailsFormProps) {
  const [draft, setDraft] = useState<DetailsDraft>({ name: "", kind: "personal", risk: null });
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

      <p role="status" className="m-0 text-base font-medium text-error empty:hidden">
        {submitError}
      </p>

      <div>
        <button type="submit" className={buttonPrimary} disabled={pending} aria-disabled={pending}>
          {pending ? "Creando…" : "Continuar"}
        </button>
      </div>
    </form>
  );
}
