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

/** Un cálculo de origen, como paso numerado de la cadena; el detalle se despliega. */
function Origin({ origin, step }: { origin: TraceOrigin; step: number }) {
  const { trace } = origin;
  return (
    <li className="trace-step relative pb-4 pl-10 last:pb-0">
      <span
        aria-hidden="true"
        className="absolute left-0 top-1.5 flex size-7 items-center justify-center rounded-full border border-line-strong bg-surface text-sm font-semibold text-ink tabular-nums"
      >
        {step}
      </span>
      {trace ? (
        <details className="rounded-control border border-line bg-surface">
          <summary className="flex min-h-touch cursor-pointer flex-wrap items-center gap-x-2 px-3 py-2 font-semibold text-ink">
            <span className="sr-only">Paso {step}: </span>
            {TRACE_KIND_LABEL[trace.kind]}
            <span className="text-sm font-normal text-ink-muted">{formatDate(trace.created_at)}</span>
          </summary>
          <div className="border-t border-line px-3 pb-4 pt-3">
            <TraceDetails trace={trace} headingLevel={5} />
          </div>
        </details>
      ) : (
        <p className="m-0 flex min-h-touch items-center text-base text-ink-muted">
          <span className="sr-only">Paso {step}: </span>
          {UNAVAILABLE}
        </p>
      )}
    </li>
  );
}

/** Cabecera: qué cálculo es y cuándo se hizo, antes del detalle. */
function Summary({ trace }: { trace: TraceChain["root"] }) {
  return (
    <div className="flex flex-col gap-1 rounded-card bg-surface-muted px-4 py-3">
      <p className="m-0 text-lg font-semibold leading-snug text-ink">{TRACE_KIND_LABEL[trace.kind]}</p>
      <p className="m-0 text-sm text-ink-muted">
        Calculado el <time dateTime={trace.created_at}>{formatDate(trace.created_at)}</time>
        {trace.sources.length > 0 &&
          ` · ${trace.sources.length} ${trace.sources.length === 1 ? "fuente" : "fuentes"}`}
      </p>
    </div>
  );
}

function Chain({ chain }: { chain: TraceChain }) {
  return (
    <>
      <Summary trace={chain.root} />
      <TraceDetails trace={chain.root} headingLevel={3} />
      {chain.origins.length > 0 && (
        <section className="flex flex-col gap-3 border-t border-line pt-5">
          <h3 className="m-0 text-base font-semibold text-ink">Cálculos de los que parte</h3>
          <ol className="trace-steps m-0 list-none p-0">
            {chain.origins.map((origin, i) => (
              <Origin key={origin.calcId} origin={origin} step={i + 1} />
            ))}
          </ol>
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
 * y los cálculos de los que parte como pasos encadenados. Todo viene de `GET /traces/{calc_id}`.
 * `<dialog>` nativo con `showModal`: atrapa el foco, cierra con Esc, deja el resto de la app
 * inerte y devuelve el foco a la cifra al cerrar. Modal centrado; pantalla completa en móvil (T5-19).
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
      className="trace-dialog m-0 h-dvh max-h-dvh w-full max-w-none overflow-y-auto overscroll-contain border-0 bg-surface p-0 text-ink backdrop:bg-black/50 sm:m-auto sm:h-auto sm:max-h-[min(90dvh,56rem)] sm:max-w-2xl sm:rounded-card sm:border sm:border-line"
    >
      <div className="flex min-h-full flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-line bg-surface px-5 py-2">
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
