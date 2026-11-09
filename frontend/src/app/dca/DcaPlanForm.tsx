import { useRef, useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiPatch, apiPost } from "../../api/client";
import type { DcaPlanOut, Frequency } from "../../api/generated/schema";
import { buttonPrimary, buttonSecondary } from "../../components/button";
import { ChoiceGroup, SelectField, TextField } from "../operations/fields";
import { AllocationFields } from "./AllocationFields";
import { buildPlan, type PlanBody, type PlanDraft, type PlanErrors } from "./planDraft";

const MONTH_DAYS = Array.from({ length: 28 }, (_, i) => ({ value: String(i + 1), label: `Día ${i + 1}` }));
const WEEK_DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"].map(
  (label, i) => ({ value: String(i + 1), label }),
);

function planErrorText(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "DCA_ALLOCATION_INVALID") {
      return "El reparto no es válido: tiene que sumar 100 %, sin activos repetidos y con cada porcentaje mayor que cero. No se ha guardado.";
    }
    if (error.code === "NOT_FOUND") return "No encontramos el plan o alguno de los activos. No se ha guardado.";
    if (error.status === 422) return "Revisa el importe, el día y el reparto. No se ha guardado.";
  }
  return "No hemos podido guardar el plan. Vuelve a intentarlo en unos segundos.";
}

interface DcaPlanFormProps {
  portfolioId: string;
  initial: PlanDraft;
  /** Si viene, se edita ese plan (PATCH); si no, se crea uno nuevo (POST). */
  plan?: DcaPlanOut;
  onDone: (plan: DcaPlanOut) => void;
  onCancel: () => void;
}

/** Crear o editar un plan de aportaciones periódicas (RF-07, UC-04). */
export function DcaPlanForm({ portfolioId, initial, plan, onDone, onCancel }: DcaPlanFormProps) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<PlanDraft>(initial);
  const [errors, setErrors] = useState<PlanErrors>({ lines: [] });
  const [errorCount, setErrorCount] = useState(0);
  const summaryRef = useRef<HTMLDivElement>(null);
  const base = `/portfolios/${encodeURIComponent(portfolioId)}/dca-plans`;

  const save = useMutation({
    mutationFn: (body: PlanBody) =>
      plan
        ? apiPatch<DcaPlanOut>(`${base}/${encodeURIComponent(plan.id)}`, body, { mock: "DcaPlanOut" })
        : apiPost<DcaPlanOut>(base, { ...body, status: "active" }, { mock: "DcaPlanOut" }),
    onSuccess: (saved) => {
      void queryClient.invalidateQueries();
      onDone(saved);
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const built = buildPlan(draft);
    if (!built.ok) {
      setErrors(built.errors);
      setErrorCount(built.count);
      requestAnimationFrame(() => summaryRef.current?.focus());
      return;
    }
    setErrors({ lines: [] });
    setErrorCount(0);
    save.mutate(built.body);
  }

  const title = plan ? "Editar plan de aportaciones" : "Nuevo plan de aportaciones";
  return (
    <form
      noValidate
      onSubmit={onSubmit}
      aria-label={title}
      className="flex flex-col gap-5 rounded-card border border-line bg-surface p-5"
    >
      <h3 className="m-0 text-lg font-semibold text-ink">{title}</h3>
      {errorCount > 0 && (
        <div
          ref={summaryRef}
          tabIndex={-1}
          role="alert"
          className="rounded-card border border-error bg-error-bg p-4 text-base font-medium text-error"
        >
          {errorCount === 1 ? "Hay 1 dato por revisar." : `Hay ${errorCount} datos por revisar.`}
        </div>
      )}
      <TextField
        label="Importe de cada aportación (€)"
        hint="Con coma para los céntimos."
        inputMode="decimal"
        autoComplete="off"
        value={draft.amount}
        onValue={(amount) => setDraft((d) => ({ ...d, amount }))}
        error={errors.amount}
      />
      <ChoiceGroup<Frequency>
        legend="Frecuencia"
        value={draft.frequency}
        options={[
          { value: "monthly", label: "Cada mes" },
          { value: "weekly", label: "Cada semana" },
        ]}
        onValue={(frequency) =>
          setDraft((d) => ({ ...d, frequency, day: frequency === "weekly" && Number(d.day) > 7 ? "1" : d.day }))
        }
      />
      <SelectField
        label={draft.frequency === "monthly" ? "Día del mes" : "Día de la semana"}
        hint={draft.frequency === "monthly" ? "Del 1 al 28, para que exista en todos los meses." : undefined}
        value={draft.day}
        options={draft.frequency === "monthly" ? MONTH_DAYS : WEEK_DAYS}
        onValue={(day) => setDraft((d) => ({ ...d, day }))}
      />
      <AllocationFields
        lines={draft.lines}
        errors={errors.lines}
        total={errors.total}
        onChange={(lines) => setDraft((d) => ({ ...d, lines }))}
      />
      <div className="flex flex-wrap gap-3">
        <button type="submit" className={buttonPrimary} disabled={save.isPending} aria-disabled={save.isPending}>
          {save.isPending ? "Guardando…" : plan ? "Guardar cambios" : "Crear plan"}
        </button>
        <button type="button" className={buttonSecondary} onClick={onCancel}>
          Cancelar
        </button>
      </div>
      <p role="status" className="m-0 text-base font-medium text-error empty:hidden">
        {save.isError ? planErrorText(save.error) : ""}
      </p>
    </form>
  );
}
