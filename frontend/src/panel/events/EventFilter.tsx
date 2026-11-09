import { useId } from "react";
import { EVENT_TYPE_LABEL, type EventType } from "../../app/news/labels";

export type EventFilterValue = "all" | EventType;

interface EventFilterProps {
  /** Tipos presentes en los eventos de la cartera: solo se ofrece lo que existe. */
  types: EventType[];
  value: EventFilterValue;
  onChange: (value: EventFilterValue) => void;
  shown: number;
  total: number;
}

/**
 * Filtro por tipo de evento: grupo de radios nativos (flechas para moverse, como el selector de
 * cartera). La opción marcada cambia de relleno, no solo de color. Un aviso `aria-live` dice
 * cuántos eventos se ven tras cada cambio.
 */
export function EventFilter({ types, value, onChange, shown, total }: EventFilterProps) {
  const name = useId();
  const options: { id: EventFilterValue; label: string }[] = [
    { id: "all", label: "Todos" },
    ...types.map((t) => ({ id: t, label: EVENT_TYPE_LABEL[t] })),
  ];
  return (
    <fieldset className="m-0 mb-4 min-w-0 border-0 p-0">
      <legend className="mb-2 p-0 text-base font-semibold text-ink">Filtrar por tipo</legend>
      <div className="flex flex-wrap items-center gap-2">
        {options.map((o) => (
          <label key={o.id} className="relative flex">
            <input
              type="radio"
              name={name}
              value={o.id}
              checked={o.id === value}
              onChange={() => onChange(o.id)}
              className="peer sr-only"
            />
            <span
              className={[
                "flex min-h-touch cursor-pointer items-center rounded-full border border-line-strong px-4 text-base font-medium text-ink-muted",
                "transition-[background-color,color,transform] duration-150 ease-out active:scale-[0.97]",
                "peer-checked:border-accent peer-checked:bg-accent peer-checked:font-semibold peer-checked:text-on-accent",
                "peer-[:not(:checked)]:hover:bg-surface-muted peer-[:not(:checked)]:hover:text-ink",
                "peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-focus",
              ].join(" ")}
            >
              {o.label}
            </span>
          </label>
        ))}
        <p role="status" aria-live="polite" className="m-0 ml-2 text-base text-ink-muted">
          {value === "all" ? `${total} ${total === 1 ? "evento" : "eventos"}` : `${shown} de ${total}`}
        </p>
      </div>
    </fieldset>
  );
}
