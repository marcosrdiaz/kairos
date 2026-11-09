import { useState } from "react";
import { buttonSecondary } from "../../components/button";
import { AssetCombobox } from "../onboarding/AssetCombobox";
import { TextField } from "../operations/fields";
import { emptyLine, refFromAsset, type AllocationLine, type PlanErrors } from "./planDraft";

interface AllocationFieldsProps {
  lines: AllocationLine[];
  errors: PlanErrors["lines"];
  total?: string | undefined;
  onChange: (lines: AllocationLine[]) => void;
}

/**
 * Reparto del plan: un activo y su porcentaje por fila. El total lo valida `buildPlan` y,
 * después, el backend (`DCA_ALLOCATION_INVALID`).
 */
export function AllocationFields({ lines, errors, total, onChange }: AllocationFieldsProps) {
  // Fila cuyo buscador debe recibir el foco (recién añadida o tras pulsar "Cambiar").
  const [focusKey, setFocusKey] = useState<number | null>(null);

  function update(key: number, patch: Partial<AllocationLine>) {
    onChange(lines.map((l) => (l.key === key ? { ...l, ...patch } : l)));
  }

  return (
    <fieldset className="m-0 flex min-w-0 flex-col gap-4 border-0 p-0" aria-describedby={total ? "dca-total-error" : undefined}>
      <legend className="mb-2 p-0 text-base font-semibold text-ink">Reparto entre activos</legend>
      {lines.map((line, i) => {
        const n = i + 1;
        const e = errors[i];
        return (
          <div key={line.key} className="flex flex-col gap-3 rounded-control border border-line p-4">
            {line.asset ? (
              <div role="group" aria-label={`Activo ${n}`} className="flex flex-col gap-2">
                <span className="text-base font-semibold text-ink">Activo {n}</span>
                <div className="flex flex-wrap items-center gap-3 rounded-control bg-surface-muted p-3">
                  <span className="flex min-w-0 flex-1 flex-col">
                    <span className="font-semibold text-ink">{line.asset.name}</span>
                    {line.asset.details && <span className="text-sm text-ink-muted">{line.asset.details}</span>}
                  </span>
                  <button
                    type="button"
                    className={buttonSecondary}
                    aria-label={`Cambiar ${line.asset.name}`}
                    onClick={() => {
                      setFocusKey(line.key);
                      update(line.key, { asset: null });
                    }}
                  >
                    Cambiar
                  </button>
                </div>
                {e?.asset && <span className="text-sm font-medium text-error">{e.asset}</span>}
              </div>
            ) : (
              <AssetCombobox
                label={`Activo ${n}`}
                value={null}
                autoFocus={line.key === focusKey}
                onChange={(asset) => asset && update(line.key, { asset: refFromAsset(asset) })}
                error={e?.asset}
              />
            )}
            <div className="flex flex-wrap items-end gap-3">
              <div className="w-full sm:w-64">
                <TextField
                  label={`Porcentaje del activo ${n} (%)`}
                  inputMode="decimal"
                  autoComplete="off"
                  value={line.percent}
                  onValue={(percent) => update(line.key, { percent })}
                  error={e?.percent}
                />
              </div>
              {lines.length > 1 && (
                <button
                  type="button"
                  className={buttonSecondary}
                  onClick={() => onChange(lines.filter((l) => l.key !== line.key))}
                >
                  Quitar activo {n}
                </button>
              )}
            </div>
          </div>
        );
      })}
      <button
        type="button"
        className={`${buttonSecondary} self-start`}
        onClick={() => {
          const line = emptyLine();
          setFocusKey(line.key);
          onChange([...lines, line]);
        }}
      >
        Añadir otro activo
      </button>
      {total && (
        <p id="dca-total-error" className="m-0 text-base font-medium text-error">
          {total}
        </p>
      )}
    </fieldset>
  );
}
