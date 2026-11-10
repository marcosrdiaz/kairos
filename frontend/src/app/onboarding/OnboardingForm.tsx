import { useEffect, useRef, useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { buttonPrimary, buttonSecondary } from "../../components/button";
import { OnboardingResult } from "./OnboardingResult";
import { PositionLineFields } from "./PositionLineFields";
import { SaveStepError, savePlan } from "./savePositions";
import { submitErrorText } from "./submitError";
import {
  buildPositions,
  emptyLine,
  todayInMadrid,
  type DraftLine,
  type DraftPlan,
  type LineErrors,
} from "./positionsDraft";

/**
 * Alta de posiciones (RF-01) en la cartera elegida: una o varias filas con activo y
 * participaciones. Sin precio, cada fila es una compra al precio de hoy (`POST /transactions`);
 * con precio medio (y fecha, opcional), va al alta `POST /positions`. El sistema completa tipo,
 * divisa, clase, TER y traspasable desde el catálogo. Errores: resumen con el foco y mensaje en
 * cada campo. `onSaved` avisa a quien lo usa (el paso 2 de crear cartera) de que ya hay posiciones.
 */
export function OnboardingForm({
  portfolioId,
  onSaved,
}: {
  portfolioId: string;
  onSaved?: () => void;
}) {
  const queryClient = useQueryClient();
  const [lines, setLines] = useState<DraftLine[]>(() => [emptyLine()]);
  const [errors, setErrors] = useState<LineErrors[]>([]);
  const [errorCount, setErrorCount] = useState(0);
  const [focusKey, setFocusKey] = useState<number | null>(null);
  const summaryRef = useRef<HTMLDivElement>(null);
  const resultRef = useRef<HTMLElement>(null);
  const today = todayInMadrid();

  const save = useMutation({
    mutationFn: (plan: DraftPlan) => savePlan(portfolioId, plan),
    onSuccess: () => {
      setLines([emptyLine()]);
      setErrors([]);
      void queryClient.invalidateQueries();
      onSaved?.();
    },
    onError: (error) => {
      // Lo ya guardado sale del formulario para no repetirlo al reintentar.
      const savedKeys = error instanceof SaveStepError ? error.savedKeys : [];
      if (savedKeys.length > 0) {
        setLines((ls) => {
          const rest = ls.filter((l) => !savedKeys.includes(l.key));
          return rest.length > 0 ? rest : [emptyLine()];
        });
        setErrors([]);
        onSaved?.();
      }
      void queryClient.invalidateQueries();
    },
  });

  // Al cambiar de cartera, el resultado anterior ya no aplica.
  const { reset } = save;
  useEffect(() => reset(), [portfolioId, reset]);

  useEffect(() => {
    if (save.isSuccess) resultRef.current?.focus();
  }, [save.isSuccess]);

  function update(key: number, patch: Partial<DraftLine>) {
    setLines((ls) => ls.map((l) => (l.key === key ? { ...l, ...patch } : l)));
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const result = buildPositions(lines, today);
    if (!result.ok) {
      setErrors(result.errors);
      setErrorCount(result.count);
      requestAnimationFrame(() => summaryRef.current?.focus());
      return;
    }
    setErrors([]);
    setErrorCount(0);
    save.mutate(result);
  }

  return (
    <div className="flex flex-col gap-5">
      {save.isSuccess && <OnboardingResult ref={resultRef} portfolio={save.data} />}
      <form noValidate onSubmit={onSubmit} className="flex flex-col gap-5">
        {errorCount > 0 && (
          <div
            ref={summaryRef}
            tabIndex={-1}
            role="alert"
            className="rounded-card border border-error bg-error-bg p-4 text-base font-medium text-error"
          >
            {errorCount === 1
              ? "Hay 1 campo por revisar."
              : `Hay ${errorCount} campos por revisar.`}{" "}
            Los verás marcados en cada posición.
          </div>
        )}
        {lines.map((line, i) => (
          <PositionLineFields
            key={line.key}
            index={i}
            line={line}
            errors={errors[i]}
            today={today}
            autoFocus={line.key === focusKey}
            onChange={(patch) => update(line.key, patch)}
            onRemove={
              lines.length > 1
                ? () => {
                    setLines((ls) => ls.filter((l) => l.key !== line.key));
                    setErrors((es) => es.filter((_, j) => j !== i));
                  }
                : undefined
            }
          />
        ))}
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className={buttonSecondary}
            onClick={() => {
              const line = emptyLine();
              setLines((ls) => [...ls, line]);
              setFocusKey(line.key);
            }}
          >
            Añadir otra posición
          </button>
          <button
            type="submit"
            className={buttonPrimary}
            disabled={save.isPending}
            aria-disabled={save.isPending}
          >
            {save.isPending
              ? "Guardando…"
              : lines.length === 1
                ? "Guardar posición"
                : `Guardar ${lines.length} posiciones`}
          </button>
        </div>
        <p role="status" className="m-0 text-base font-medium text-error empty:hidden">
          {save.isError ? submitErrorText(save.error, lines) : ""}
        </p>
      </form>
    </div>
  );
}
