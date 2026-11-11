import { useId, type CSSProperties } from "react";
import type { HistoryPeriod } from "../../../api/generated/schema";
import { PERIODS } from "./chartFormat";

interface PeriodPickerProps {
  value: HistoryPeriod;
  onChange: (period: HistoryPeriod) => void;
}

/**
 * Selector de periodo: radios nativos con aspecto de control segmentado y una píldora dorada que
 * se desliza hasta la opción elegida. Las flechas cambian de opción (comportamiento nativo) y el
 * lector anuncia el nombre completo («Última semana»). En móvil ocupa todo el ancho.
 */
export function PeriodPicker({ value, onChange }: PeriodPickerProps) {
  const name = useId();
  const index = Math.max(0, PERIODS.findIndex((p) => p.value === value));
  const style = { "--count": PERIODS.length, "--index": index } as CSSProperties;
  return (
    <fieldset className="kchart-period m-0 w-full min-w-0" style={style}>
      <legend className="sr-only">Periodo de la gráfica</legend>
      <span className="kchart-period-pill" aria-hidden="true" />
      {PERIODS.map((p) => (
        <label
          key={p.value}
          className="relative z-10 flex min-h-touch cursor-pointer items-center justify-center rounded-full px-3 text-sm font-semibold text-ink-muted transition-colors duration-200 hover:text-ink sm:min-w-14"
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
