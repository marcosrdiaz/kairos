import { useEffect, useId, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { ApiError } from "../../api/client";
import { getTrace } from "../../api/trace";
import { formatDate } from "../../lib/format";
import { buttonSecondary } from "../button";
import { TraceDetails } from "./TraceDetails";
import { TRACE_KIND_LABEL } from "./labels";
import { loadTraceChain, type TraceChain, type TraceOrigin } from "./traceChain";

const UNAVAILABLE = "Traza no disponible";

function Origin({ origin }: { origin: TraceOrigin }) {
  const { trace } = origin;
  if (!trace) return <li className="py-3 text-base text-ink-muted">{UNAVAILABLE}</li>;
  return (
    <li>
      <details className="py-1">
        <summary className="flex min-h-touch cursor-pointer flex-wrap items-center gap-x-2 font-semibold text-ink">
          {TRACE_KIND_LABEL[trace.kind]}
          <span className="text-sm font-normal text-ink-muted">{formatDate(trace.created_at)}</span>
        </summary>
        <div className="pb-4 pt-2">
          <TraceDetails trace={trace} headingLevel={5} />
        </div>
      </details>
    </li>
  );
}

function Chain({ chain }: { chain: TraceChain }) {
  return (
    <>
      <p className="m-0 text-lg font-semibold text-ink">{TRACE_KIND_LABEL[chain.root.kind]}</p>
      <TraceDetails trace={chain.root} headingLevel={3} />
      {chain.origins.length > 0 && (
        <section className="mt-2 border-t border-line pt-5">
          <h3 className="m-0 text-base font-semibold text-ink">Cálculos de los que parte</h3>
          <ul className="m-0 list-none divide-y divide-line p-0">
            {chain.origins.map((origin) => (
              <Origin key={origin.calcId} origin={origin} />
            ))}
          </ul>
          {chain.truncated && (
            <p className="m-0 mt-2 text-sm text-ink-muted">
              Hay más cálculos de origen que no se muestran aquí.
            </p>
          )}
        </section>
      )}
    </>
  );
}

function Failure({ error, onRetry }: { error: Error; onRetry: () => void }) {
  if (error instanceof ApiError && error.status === 404) {
    return (
      <p className="m-0 text-base text-ink-muted">
        {UNAVAILABLE}. No tenemos guardado el detalle de este cálculo.
      </p>
    );
  }
  return (
    <div className="flex flex-col items-start gap-3">
      <p role="alert" className="m-0 text-base text-error">
        No hemos podido cargar el detalle de este cálculo.
      </p>
      <button type="button" className={buttonSecondary} onClick={onRetry}>
        Reintentar
      </button>
    </div>
  );
}

interface TraceDialogProps {
  calcId: string;
  onClose: () => void;
}

/**
 * «¿De dónde sale?» (RF-19, UC-10): entradas, fórmula, resultado, fuentes y fecha de una cifra,
 * y los cálculos de los que parte. Todo viene de `GET /traces/{calc_id}`.
 * `<dialog>` nativo con `showModal`: atrapa el foco, cierra con Esc, deja el resto de la app
 * inerte y devuelve el foco a la cifra al cerrar.
 */
export function TraceDialog({ calcId, onClose }: TraceDialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const { data, error, refetch } = useQuery({
    queryKey: ["trace-chain", calcId],
    queryFn: ({ signal }) => loadTraceChain(calcId, (id) => getTrace(id, signal)),
    staleTime: Infinity, // una traza no cambia una vez creada
    retry: false,
  });

  useEffect(() => {
    if (ref.current && !ref.current.open) ref.current.showModal();
  }, []);

  const close = () => ref.current?.close();

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === event.currentTarget) close(); // clic en el fondo
      }}
      className="m-0 ml-auto h-dvh max-h-dvh w-full max-w-xl overflow-y-auto border-0 border-l border-line bg-surface p-0 text-ink backdrop:bg-black/50"
    >
      <div className="flex min-h-full flex-col">
        <header className="sticky top-0 flex items-center justify-between gap-3 border-b border-line bg-surface px-5 py-2">
          <h2 id={titleId} className="m-0 text-xl font-semibold text-ink">
            ¿De dónde sale esta cifra?
          </h2>
          <button
            type="button"
            aria-label="Cerrar"
            onClick={close}
            className="flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full text-2xl leading-none text-ink-muted hover:bg-surface-muted"
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>
        <div className="flex flex-col gap-5 px-5 py-5">
          {data && <Chain chain={data} />}
          {error && <Failure error={error} onRetry={() => void refetch()} />}
          {!data && !error && (
            <p role="status" className="m-0 text-base text-ink-muted">
              Cargando el cálculo…
            </p>
          )}
        </div>
      </div>
    </dialog>
  );
}
