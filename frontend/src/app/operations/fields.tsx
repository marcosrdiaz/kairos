import { useId, type InputHTMLAttributes } from "react";

const control =
  "min-h-touch w-full rounded-control border border-line-strong bg-surface px-3 text-base text-ink aria-invalid:border-error";

function describedBy(id: string, hint?: string, error?: string): string | undefined {
  return [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ") || undefined;
}

function HintAndError({ id, hint, error }: { id: string; hint?: string | undefined; error?: string | undefined }) {
  return (
    <>
      {hint && (
        <span id={`${id}-hint`} className="text-sm text-ink-muted">
          {hint}
        </span>
      )}
      {error && (
        <span id={`${id}-error`} className="text-sm font-medium text-error">
          {error}
        </span>
      )}
    </>
  );
}

interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value"> {
  label: string;
  hint?: string | undefined;
  error?: string | undefined;
  value: string;
  onValue: (value: string) => void;
}

/** Campo de texto con etiqueta, pista y error enlazados por aria-describedby. */
export function TextField({ label, hint, error, value, onValue, ...input }: TextFieldProps) {
  const id = useId();
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <label htmlFor={id} className="text-base font-semibold text-ink">
        {label}
      </label>
      <input
        id={id}
        value={value}
        onChange={(e) => onValue(e.target.value)}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        className={control}
        {...input}
      />
      <HintAndError id={id} hint={hint} error={error} />
    </div>
  );
}

export interface Option {
  value: string;
  label: string;
}

interface SelectFieldProps {
  label: string;
  hint?: string | undefined;
  error?: string | undefined;
  value: string;
  options: Option[];
  /** Texto de la opción vacía; si falta, no hay opción vacía. */
  placeholder?: string;
  onValue: (value: string) => void;
}

/** Desplegable nativo (teclado y lector de pantalla sin trabajo extra). */
export function SelectField({ label, hint, error, value, options, placeholder, onValue }: SelectFieldProps) {
  const id = useId();
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <label htmlFor={id} className="text-base font-semibold text-ink">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onValue(e.target.value)}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        className={control}
      >
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <HintAndError id={id} hint={hint} error={error} />
    </div>
  );
}

interface ChoiceGroupProps<T extends string> {
  legend: string;
  value: T;
  options: { value: T; label: string }[];
  onValue: (value: T) => void;
}

/**
 * Grupo de radios nativos con aspecto de pastillas (mismo patrón que el selector de cartera):
 * flechas para moverse; la opción marcada cambia de relleno, no solo de color.
 */
export function ChoiceGroup<T extends string>({ legend, value, options, onValue }: ChoiceGroupProps<T>) {
  const name = useId();
  return (
    <fieldset className="m-0 min-w-0 border-0 p-0">
      <legend className="mb-2 p-0 text-base font-semibold text-ink">{legend}</legend>
      <div className="grid w-full grid-cols-2 gap-1 rounded-[1.75rem] border border-line-strong bg-surface p-1 @3xl/app-content:inline-grid @3xl/app-content:w-fit">
        {options.map((o) => (
          <label key={o.value} className="relative flex min-w-0">
            <input
              type="radio"
              name={name}
              value={o.value}
              checked={o.value === value}
              onChange={() => onValue(o.value)}
              className="peer sr-only"
            />
            <span
              className={[
                "flex min-h-touch min-w-0 cursor-pointer items-center justify-center rounded-full px-2 text-center text-base leading-tight font-medium text-ink-muted transition-colors @3xl/app-content:px-5",
                "peer-checked:bg-accent peer-checked:font-semibold peer-checked:text-on-accent",
                "peer-[:not(:checked)]:hover:bg-surface-muted peer-[:not(:checked)]:hover:text-ink",
                "peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-focus",
              ].join(" ")}
            >
              {o.label}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
