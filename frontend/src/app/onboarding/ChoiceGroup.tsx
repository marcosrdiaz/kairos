import { useId } from "react";

interface ChoiceGroupProps<T extends string> {
  legend: string;
  options: { value: T; label: string; hint: string }[];
  value: T | null;
  onChange: (value: T) => void;
  error?: string | undefined;
}

/**
 * Grupo de radios nativos con aspecto de tarjeta: flechas para moverse y el lector anuncia
 * "<leyenda>, grupo, <opción>, 1 de N". La elegida cambia de borde y de relleno, no solo de color.
 */
export function ChoiceGroup<T extends string>({
  legend,
  options,
  value,
  onChange,
  error,
}: ChoiceGroupProps<T>) {
  const name = useId();
  const errorId = `${name}-error`;
  return (
    <fieldset
      className="m-0 flex min-w-0 flex-col gap-2 border-0 p-0"
      aria-invalid={error ? true : undefined}
      aria-describedby={error ? errorId : undefined}
    >
      <legend className="mb-2 p-0 text-base font-semibold text-ink">{legend}</legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {options.map((o) => (
          <label key={o.value} className="relative flex">
            <input
              type="radio"
              name={name}
              value={o.value}
              checked={value === o.value}
              onChange={() => onChange(o.value)}
              className="peer sr-only"
            />
            <span
              className={[
                "flex min-h-touch w-full cursor-pointer flex-col gap-0.5 rounded-control border border-line-strong bg-surface px-4 py-3 transition-colors",
                "peer-checked:border-accent peer-checked:bg-accent-tint",
                "peer-[:not(:checked)]:hover:bg-surface-muted",
                "peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-focus",
              ].join(" ")}
            >
              <span className="text-base font-semibold text-ink">{o.label}</span>
              <span className="text-sm text-ink-muted">{o.hint}</span>
            </span>
          </label>
        ))}
      </div>
      {error && (
        <span id={errorId} className="text-sm font-medium text-error">
          {error}
        </span>
      )}
    </fieldset>
  );
}
