import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { ApiError } from "../../api/client";
import { getTrace } from "../../api/trace";
import type { TraceOut } from "../../api/generated/schema";
import { formatDate } from "../../lib/format";
import { TRACE_KIND_LABEL } from "./labels";

const MAX_SOURCES = 2;

interface TraceCardBodyProps {
  calcId: string;
  /** La cifra tal como se ve en la pantalla (ya formateada). `undefined` en `TraceLink`. */
  value: ReactNode;
  /** Id del resumen (explicación, fecha y fuentes): la cifra lo usa como `aria-describedby`. */
  summaryId: string;
  onFull: () => void;
}

function Sources({ sources }: { sources: TraceOut["sources"] }) {
  if (sources.length === 0) return null;
  const shown = sources.slice(0, MAX_SOURCES);
  const rest = sources.length - shown.length;
  return (
    <span role="list" aria-label="Fuentes" className="mt-2 flex flex-col gap-1 border-t border-line pt-2">
      {shown.map((source) => (
        <span role="listitem" key={`${source.kind}:${source.ref}`} className="block">
          <span className="block text-ink">{source.label}</span>
          {source.as_of && <span className="block text-xs text-ink-muted">Dato a {formatDate(source.as_of)}</span>}
        </span>
      ))}
      {rest > 0 && (
        <span className="block text-xs text-ink-muted">
          y {rest} {rest === 1 ? "fuente más" : "fuentes más"}
        </span>
      )}
    </span>
  );
}

/**
 * Contenido de la tarjeta de una cifra (T5-18): valor, explicación (qué cálculo es), fecha del
 * cálculo y fuentes, de `GET /traces/{calc_id}`. La traza entera (entradas, fórmula, cálculos de
 * origen) sigue en la hoja de `TraceDialog`. Solo `<span>`: la cifra suele ir dentro de un `<p>`.
 */
export function TraceCardBody({ calcId, value, summaryId, onFull }: TraceCardBodyProps) {
  const { data, error } = useQuery({
    queryKey: ["trace", calcId],
    queryFn: ({ signal }) => getTrace(calcId, signal),
    staleTime: Infinity, // una traza no cambia una vez creada
    retry: false,
  });
  const missing = error instanceof ApiError && error.status === 404;

  return (
    <>
      {value !== undefined && (
        <span className="block text-xl font-semibold leading-tight text-ink tabular-nums">{value}</span>
      )}
      <span id={summaryId} className="block text-sm">
        {data && (
          <>
            <span className="block font-semibold text-ink">{TRACE_KIND_LABEL[data.kind]}</span>
            <span className="block text-ink-muted">
              Calculado el <time dateTime={data.created_at}>{formatDate(data.created_at)}</time>
            </span>
            <Sources sources={data.sources} />
          </>
        )}
        {missing && (
          <span className="block text-ink-muted">Traza no disponible. No tenemos guardado el detalle de este cálculo.</span>
        )}
        {error && !missing && <span className="block text-error">No hemos podido cargar el detalle de este cálculo.</span>}
        {!data && !error && <span className="block text-ink-muted">Cargando el cálculo…</span>}
      </span>
      {!missing && (
        <button
          type="button"
          onClick={onFull}
          className="mt-1 inline-flex min-h-touch cursor-pointer items-center self-start border-0 bg-transparent p-0 text-sm font-semibold text-accent underline"
        >
          Ver el cálculo completo
        </button>
      )}
    </>
  );
}
