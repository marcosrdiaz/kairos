import { useId } from "react";
import { ArrowRightIcon, CoinsIcon, WalletIcon } from "../../components/icons";
import type { OperationKind } from "./operationDraft";

const KINDS: {
  value: OperationKind;
  label: string;
  description: string;
  Icon: typeof CoinsIcon;
  tone: string;
}[] = [
  {
    value: "buy",
    label: "Compra",
    description: "Anota una compra ya realizada.",
    Icon: CoinsIcon,
    tone: "bg-icon-gold-bg text-icon-gold",
  },
  {
    value: "sell",
    label: "Venta",
    description: "Anota una venta ya realizada.",
    Icon: WalletIcon,
    tone: "bg-icon-red-bg text-icon-red",
  },
  {
    value: "transfer",
    label: "Traspaso",
    description: "Entre fondos de inversión.",
    Icon: ArrowRightIcon,
    tone: "bg-icon-blue-bg text-icon-blue",
  },
];

export function OperationKindPicker({
  value,
  onValue,
}: {
  value: OperationKind;
  onValue: (value: OperationKind) => void;
}) {
  const name = useId();
  return (
    <fieldset className="m-0 min-w-0 border-0 p-0">
      <legend className="mb-2 p-0 text-base font-semibold text-ink">Tipo de operación</legend>
      <div className="grid min-w-0 grid-cols-1 gap-2 @3xl/app-content:inline-grid @3xl/app-content:w-fit @3xl/app-content:grid-cols-3">
        {KINDS.map(({ value: kind, label, description, Icon, tone }) => (
          <label key={kind} className="relative min-w-0 cursor-pointer">
            <input
              type="radio"
              name={name}
              value={kind}
              checked={kind === value}
              onChange={() => onValue(kind)}
              aria-label={label}
              aria-describedby={`${name}-${kind}-description`}
              className="peer sr-only"
            />
            <span className="flex items-start gap-3 rounded-control border border-line bg-surface p-3 transition-colors hover:border-line-strong peer-checked:border-accent peer-checked:bg-accent-tint peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-focus">
              <span className={`mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-control ${tone}`}>
                <Icon className="size-5" />
              </span>
              <span className="flex min-w-0 flex-col gap-1">
                <span className="font-semibold text-ink">{label}</span>
                <span id={`${name}-${kind}-description`} className="text-sm text-ink-muted">
                  {description}
                </span>
              </span>
            </span>
            <svg
              aria-hidden="true"
              focusable="false"
              viewBox="0 0 16 16"
              className="pointer-events-none absolute right-3 top-3 size-4 text-accent opacity-0 peer-checked:opacity-100"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m3 8 3 3 7-7" />
            </svg>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
