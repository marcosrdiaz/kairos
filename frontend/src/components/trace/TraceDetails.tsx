import type { ReactNode } from "react";
import type { TraceOut } from "../../api/generated/schema";
import { formatDate } from "../../lib/format";
import { TRACE_KIND_HOW } from "./labels";
import { toTraceFields, type TraceField } from "./traceFields";

/**
 * Datos de un cálculo como lista agrupada: nombre a la izquierda y valor a la derecha (en móvil,
 * uno debajo de otro); los grupos anidados van sangrados bajo su nombre. `strong` resalta los
 * valores (el resultado).
 */
function FieldList({ fields, nested = false, strong = false }: {
  fields: TraceField[];
  nested?: boolean;
  strong?: boolean;
}) {
  const value = strong ? "text-lg font-semibold" : "text-base";
  const divider = strong ? "divide-y divide-accent-tint-strong" : "divide-y divide-line";
  return (
    <dl className={`m-0 flex flex-col ${nested ? "" : divider}`}>
      {fields.map((field) =>
        "text" in field ? (
          <div
            key={field.key}
            className={`grid items-baseline gap-x-4 gap-y-0.5 sm:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] ${nested ? "py-1" : "px-4 py-2.5"}`}
          >
            <dt className="text-sm text-ink-muted">{field.label}</dt>
            <dd className={`m-0 break-words text-ink tabular-nums sm:text-right ${value}`}>{field.text}</dd>
          </div>
        ) : (
          <div key={field.key} className={nested ? "py-1" : "px-4 py-2.5"}>
            <dt className="text-sm font-semibold text-ink">{field.label}</dt>
            <dd className={`m-0 mt-1 pl-3 ${nested ? "" : "border-l border-line-strong"}`}>
              <FieldList fields={field.fields} nested strong={strong} />
            </dd>
          </div>
        ),
      )}
    </dl>
  );
}

function Block({ title, hint, level, children }: {
  title: string;
  hint: string;
  level: 3 | 5;
  children: ReactNode;
}) {
  const Heading = level === 3 ? "h3" : "h5";
  return (
    <section className="flex flex-col gap-2.5">
      <div className="flex flex-col gap-0.5">
        <Heading className="m-0 text-base font-semibold text-ink">{title}</Heading>
        <p className="m-0 text-sm text-ink-muted">{hint}</p>
      </div>
      {children}
    </section>
  );
}

const EMPTY = <p className="m-0 text-base text-ink-muted">Sin datos.</p>;
const PANEL = "overflow-hidden rounded-control border border-line bg-surface";

function Fields({ record, strong = false }: { record: Record<string, unknown>; strong?: boolean }) {
  const fields = toTraceFields(record);
  if (fields.length === 0) return EMPTY;
  return (
    <div className={strong ? "trace-result overflow-hidden rounded-control border border-accent-tint-strong bg-accent-tint" : PANEL}>
      <FieldList fields={fields} strong={strong} />
    </div>
  );
}

function ExternalIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" className="size-3.5 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.5 2.5h4v4M13.5 2.5 7 9M12 9.5v3a1 1 0 0 1-1 1H3.5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h3" />
    </svg>
  );
}

function Sources({ sources }: { sources: TraceOut["sources"] }) {
  if (sources.length === 0) return EMPTY;
  return (
    <ul className={`${PANEL} m-0 flex list-none flex-col divide-y divide-line p-0`}>
      {sources.map((source) => (
        <li key={`${source.kind}:${source.ref}`} className="flex flex-col gap-0.5 px-4 py-2.5">
          {source.url && /^https?:\/\//.test(source.url) ? (
            <a
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 self-start text-base text-accent underline underline-offset-2"
            >
              {source.label}
              <ExternalIcon />
              <span className="sr-only">(se abre en una pestaña nueva)</span>
            </a>
          ) : (
            <span className="text-base text-ink">{source.label}</span>
          )}
          {source.as_of && <span className="text-sm text-ink-muted">Dato a {formatDate(source.as_of)}</span>}
        </li>
      ))}
    </ul>
  );
}

interface TraceDetailsProps {
  trace: TraceOut;
  headingLevel: 3 | 5;
}

/**
 * Un cálculo, en el orden de UC-10: entradas, fórmula, resultado, fuentes y fecha. Cada bloque dice
 * para qué sirve; la fórmula se explica en palabras y la exacta queda a un clic (T5-19).
 */
export function TraceDetails({ trace, headingLevel }: TraceDetailsProps) {
  return (
    <div className="flex flex-col gap-6">
      <Block title="Entradas" hint="Los datos de los que parte el cálculo." level={headingLevel}>
        <Fields record={trace.inputs} />
      </Block>
      <Block title="Fórmula" hint="Cómo se combinan esos datos." level={headingLevel}>
        <p className="m-0 max-w-[65ch] text-base text-ink">{TRACE_KIND_HOW[trace.kind]}</p>
        <details className="trace-formula group">
          <summary className="inline-flex min-h-touch cursor-pointer items-center gap-1.5 text-sm font-semibold text-accent">
            <svg aria-hidden="true" viewBox="0 0 16 16" className="size-3.5 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="m6 3.5 4.5 4.5L6 12.5" />
            </svg>
            Ver la fórmula exacta
          </summary>
          <code className="mt-1 block whitespace-pre-wrap break-words rounded-control bg-surface-muted px-3 py-2.5 text-sm leading-relaxed text-ink">
            {trace.formula}
          </code>
        </details>
      </Block>
      <Block title="Resultado" hint="Lo que sale del cálculo: la cifra que ves en la pantalla." level={headingLevel}>
        <Fields record={trace.outputs} strong />
      </Block>
      <Block title="Fuentes" hint="De dónde salen los datos de partida, con su fecha." level={headingLevel}>
        <Sources sources={trace.sources} />
      </Block>
      <Block title="Fecha del cálculo" hint="Cuándo se hizo esta cuenta." level={headingLevel}>
        <p className="m-0 text-base text-ink">
          <time dateTime={trace.created_at}>{formatDate(trace.created_at)}</time>
        </p>
      </Block>
    </div>
  );
}
