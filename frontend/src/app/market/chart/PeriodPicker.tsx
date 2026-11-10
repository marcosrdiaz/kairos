import { useId } from "react";
import type { HistoryPeriod } from "../../../api/generated/schema";
import { PERIODS } from "./chartFormat";

interface PeriodPickerProps {
  value: HistoryPeriod;
  onChange: (period: HistoryPeriod) => void;
}

/**
 * Selector de periodo: grupo de radios nativos con aspecto de botones segmentados.
 * Las flechas cambian de opción (comportamiento nativo) y el lector anuncia el nombre completo.
 */
export function PeriodPicker({ value, onChange }: PeriodPickerProps) {
  const name = useId();
  return (
    <fieldset className="m-0 flex rounded-full border border-line bg-surface-muted p-1">
      <legend className="sr-only">Periodo de la gráfica</legend>
      {PERIODS.map((p) => (
        <label
          key={p.value}
          className="relative flex min-h-touch min-w-12 cursor-pointer items-center justify-center rounded-full px-3 text-sm font-semibold text-ink-muted transition-colors has-[:checked]:bg-accent has-[:checked]:text-on-accent has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-focus hover:text-ink has-[:checked]:hover:text-on-accent"
        >
          <input
            type="radio"
            name={name}
            value={p.value}
            checked={value === p.value}
            onChange={() => onChange(p.value)}
            aria-label={p.name}
            className="sr-only"
          />
          <span aria-hidden="true">{p.label}</span>
        </label>
      ))}
    </fieldset>
  );
}
