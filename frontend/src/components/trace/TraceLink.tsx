import { TraceAnchor } from "./TraceAnchor";
import { useTrace } from "./traceContext";

interface TraceLinkProps {
  calcId?: string | null | undefined;
  label?: string;
  className?: string;
}

/**
 * «¿De dónde sale?» como enlace de texto, para frases y tarjetas donde la cifra no es tocable. Abre
 * la misma tarjeta que `TraceFigure` (T5-18), sin cifra arriba.
 */
export function TraceLink({ calcId, label = "¿De dónde sale?", className = "" }: TraceLinkProps) {
  const trace = useTrace();
  if (!calcId || !trace) return null;
  return (
    <TraceAnchor
      calcId={calcId}
      triggerClassName={`inline-flex min-h-touch cursor-pointer items-center border-0 bg-transparent p-0 text-base font-semibold text-accent underline ${className}`}
    >
      {label}
    </TraceAnchor>
  );
}
