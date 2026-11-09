import { createContext, use } from "react";

export interface TraceOpener {
  open: (calcId: string) => void;
}

export const TraceContext = createContext<TraceOpener | null>(null);

/** Abre la traza de una cifra. `null` fuera de `TraceProvider`: la cifra se pinta sin enlace. */
export function useTrace(): TraceOpener | null {
  return use(TraceContext);
}
