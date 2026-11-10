import { useId, useState, type InputHTMLAttributes } from "react";
import { buttonSecondary } from "../../components/button";
import { AssetCombobox } from "./AssetCombobox";
import type { DraftLine, LineErrors } from "./positionsDraft";

interface FieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value"> {
  label: string;
  hint?: string;
  error?: string | undefined;
  value: string;
  onValue: (value: string) => void;
}

/** Campo con etiqueta, pista y error enlazados por aria-describedby. */
function Field({ label, hint, error, value, onValue, ...input }: FieldProps) {
  const id = useId();
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ");
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
        aria-describedby={describedBy || undefined}
        className="min-h-touch w-full rounded-control border border-line-strong bg-surface px-3 text-base text-ink aria-invalid:border-error"
        {...input}
      />
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
    </div>
  );
}

interface PositionLineFieldsProps {
  index: number;
  line: DraftLine;
  errors: LineErrors | undefined;
  today: string;
  autoFocus: boolean;
  onChange: (patch: Partial<DraftLine>) => void;
  /** Ausente si es la única fila. */
  onRemove?: (() => void) | undefined;
}

/**
 * Una posición del alta: activo y participaciones. El precio medio y la fecha de compra van
 * plegados y son opcionales; sin precio, la posición se registra al precio de hoy. La parte
 * plegada se abre sola si tiene datos o errores, para que nunca se oculte un error.
 */
export function PositionLineFields({
  index,
  line,
  errors,
  today,
  autoFocus,
  onChange,
  onRemove,
}: PositionLineFieldsProps) {
  const n = index + 1;
  const panelId = useId();
  const [open, setOpen] = useState(() => Boolean(line.cost || line.date));
  const shown = open || Boolean(errors?.cost || errors?.date);
  const priced = line.cost.trim() !== "";
  return (
    <fieldset className="m-0 flex min-w-0 flex-col gap-4 rounded-card border border-line bg-surface p-5">
      <legend className="px-1 text-lg font-semibold text-ink">Posición {n}</legend>
      <AssetCombobox
        label="Activo"
        value={line.asset}
        onChange={(asset) => onChange({ asset })}
        error={errors?.asset}
        autoFocus={autoFocus}
      />
      <div className="sm:max-w-xs">
        <Field
          label="Participaciones"
          hint={
            priced
              ? "Con coma para los decimales."
              : "Con coma para los decimales. Se registra al precio de hoy."
          }
          inputMode="decimal"
          autoComplete="off"
          value={line.units}
          onValue={(units) => onChange({ units })}
          error={errors?.units}
        />
      </div>
      <div className="flex flex-col gap-4">
        <button
          type="button"
          aria-expanded={shown}
          aria-controls={panelId}
          onClick={() => setOpen(!shown)}
          className="inline-flex min-h-touch items-center gap-2 self-start rounded-control px-1 text-base font-semibold text-accent underline underline-offset-4 hover:text-accent-hover"
        >
          <span aria-hidden="true">{shown ? "−" : "+"}</span>
          Indicar precio de compra y fecha (opcional)
        </button>
        {shown && (
          <div id={panelId} className="grid gap-4 sm:grid-cols-2">
            <Field
              label="Precio medio (€)"
              hint="Lo que te costó cada participación. Vacío: precio de hoy."
              inputMode="decimal"
              autoComplete="off"
              value={line.cost}
              onValue={(cost) => onChange({ cost })}
              error={errors?.cost}
            />
            <Field
              label="Fecha de compra"
              hint="Solo con precio de compra. Si la dejas vacía, hoy."
              type="date"
              max={today}
              value={line.date}
              onValue={(date) => onChange({ date })}
              error={errors?.date}
            />
          </div>
        )}
      </div>
      {onRemove && (
        <button type="button" className={`${buttonSecondary} self-start`} onClick={onRemove}>
          Quitar posición {n}
        </button>
      )}
    </fieldset>
  );
}
