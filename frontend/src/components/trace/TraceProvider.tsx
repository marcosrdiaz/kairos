import { useMemo, useState, type ReactNode } from "react";
import { TraceDialog } from "./TraceDialog";
import { TraceContext } from "./traceContext";

/** Una sola hoja de traza para toda la app. Se monta por encima de las rutas (`App.tsx`). */
export function TraceProvider({ children }: { children: ReactNode }) {
  const [calcId, setCalcId] = useState<string | null>(null);
  const opener = useMemo(() => ({ open: setCalcId }), []);
  return (
    <TraceContext value={opener}>
      {children}
      {calcId !== null && <TraceDialog key={calcId} calcId={calcId} onClose={() => setCalcId(null)} />}
    </TraceContext>
  );
}
