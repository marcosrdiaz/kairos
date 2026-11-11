import type { ReactNode } from "react";
import { TraceAnchor } from "./TraceAnchor";
import { useTrace } from "./traceContext";

interface TraceFigureProps {
  /** `calc_id` de la cifra; si el backend no lo da, se pinta sin enlace. */
  calcId?: string | null | undefined;
  children: ReactNode;
}

/**
 * Una cifra que se explica al pasar el ratón, enfocarla o tocarla (T5-18): hereda el tipo de letra
 * y solo añade un subrayado punteado. Un botón por cifra y no un enlace aparte, para no llenar las
 * tablas. La tarjeta repite la cifra arriba y lleva a la traza completa.
 */
export function TraceFigure({ calcId, children }: TraceFigureProps) {
  const trace = useTrace();
  if (!calcId || !trace) return <span data-calc-id={calcId ?? undefined}>{children}</span>;
  return (
    <TraceAnchor
      calcId={calcId}
      value={children}
      triggerClassName="cursor-pointer rounded-sm border-0 bg-transparent p-0 text-left [font:inherit] text-inherit underline decoration-line-strong decoration-dotted underline-offset-4 hover:decoration-accent aria-expanded:decoration-accent"
    >
      {children}
      <span className="sr-only"> ¿De dónde sale?</span>
    </TraceAnchor>
  );
}
