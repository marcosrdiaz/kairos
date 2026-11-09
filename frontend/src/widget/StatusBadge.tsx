import type { StatusState } from "../api/generated/schema";
import { STATE_WORD, stateClasses } from "./states";

interface StatusBadgeProps {
  state: StatusState;
  label?: string;
}

/** Insignia de estado: color de estado + palabra. */
export function StatusBadge({ state, label }: StatusBadgeProps) {
  return (
    <span
      data-state={state}
      className={`inline-flex min-h-touch items-center gap-2 rounded-full px-4 text-base font-semibold ${stateClasses(state)}`}
    >
      <span aria-hidden="true" className="size-2.5 rounded-full bg-current" />
      {label || STATE_WORD[state]}
    </span>
  );
}
