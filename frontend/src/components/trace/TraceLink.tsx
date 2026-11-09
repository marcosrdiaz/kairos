import { useTrace } from "./traceContext";

interface TraceLinkProps {
  calcId?: string | null | undefined;
  label?: string;
  className?: string;
}

/** «¿De dónde sale?» como enlace de texto, para frases y tarjetas donde la cifra no es tocable. */
export function TraceLink({ calcId, label = "¿De dónde sale?", className = "" }: TraceLinkProps) {
  const trace = useTrace();
  if (!calcId || !trace) return null;
  return (
    <button
      type="button"
      onClick={() => trace.open(calcId)}
      className={`inline-flex min-h-touch cursor-pointer items-center border-0 bg-transparent p-0 text-base font-semibold text-accent underline ${className}`}
    >
      {label}
    </button>
  );
}
