import type { ReactNode } from "react";
import type { TraceOut } from "../../api/generated/schema";
import { formatDate } from "../../lib/format";
import { toTraceFields, type TraceField } from "./traceFields";

/**
 * Datos de un cálculo como lista agrupada: nombre a la izquierda y valor a la derecha (en móvil,
 * uno debajo de otro); los grupos anidados van sangrados bajo su nombre.
 */
function FieldList({ fields, nested = false }: { fields: TraceField[]; nested?: boolean }) {
  return (
    <dl className={`m-0 flex flex-col ${nested ? "" : "divide-y divide-line rounded-control border border-line"}`}>
      {fields.map((field) =>
        "text" in field ? (
          <div
            key={field.key}
            className={`grid gap-x-4 gap-y-0.5 sm:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] ${nested ? "py-1" : "px-3 py-2"}`}
          >
            <dt className="text-sm text-ink-muted">{field.label}</dt>
            <dd className="m-0 break-words text-base text-ink tabular-nums sm:text-right">{field.text}</dd>
          </div>
        ) : (
          <div key={field.key} className={nested ? "py-1" : "px-3 py-2"}>
            <dt className="text-sm font-semibold text-ink">{field.label}</dt>
            <dd className="m-0 mt-1 border-l-2 border-line pl-3">
              <FieldList fields={field.fields} nested />
            </dd>
          </div>
        ),
      )}
    </dl>
  );
}

function Block({ title, level, children }: { title: string; level: 3 | 5; children: ReactNode }) {
  const Heading = level === 3 ? "h3" : "h5";
  return (
    <section className="flex flex-col gap-2">
      <Heading className="m-0 text-base font-semibold text-ink">{title}</Heading>
      {children}
    </section>
  );
}

const EMPTY = <p className="m-0 text-base text-ink-muted">Sin datos.</p>;

function Fields({ record }: { record: Record<string, unknown> }) {
  const fields = toTraceFields(record);
  return fields.length > 0 ? <FieldList fields={fields} /> : EMPTY;
}

function Sources({ sources }: { sources: TraceOut["sources"] }) {
  if (sources.length === 0) return EMPTY;
  return (
    <ul className="m-0 flex list-none flex-col gap-2 p-0">
      {sources.map((source) => (
        <li key={`${source.kind}:${source.ref}`} className="text-base text-ink">
          {source.url && /^https?:\/\//.test(source.url) ? (
            <a href={source.url} target="_blank" rel="noreferrer" className="text-accent underline">
              {source.label}
            </a>
          ) : (
            source.label
          )}
          {source.as_of && (
            <span className="block text-sm text-ink-muted">Dato a {formatDate(source.as_of)}</span>
          )}
        </li>
      ))}
    </ul>
  );
}

interface TraceDetailsProps {
  trace: TraceOut;
  headingLevel: 3 | 5;
}

/** Un cálculo, en el orden de UC-10: entradas, fórmula, resultado, fuentes y fecha. */
export function TraceDetails({ trace, headingLevel }: TraceDetailsProps) {
  return (
    <div className="flex flex-col gap-5">
      <Block title="Entradas" level={headingLevel}>
        <Fields record={trace.inputs} />
      </Block>
      <Block title="Fórmula" level={headingLevel}>
        <code className="block whitespace-pre-wrap break-words rounded-control bg-surface-muted px-3 py-2.5 text-sm leading-relaxed text-ink">
          {trace.formula}
        </code>
      </Block>
      <Block title="Resultado" level={headingLevel}>
        <Fields record={trace.outputs} />
      </Block>
      <Block title="Fuentes" level={headingLevel}>
        <Sources sources={trace.sources} />
      </Block>
      <Block title="Fecha del cálculo" level={headingLevel}>
        <p className="m-0 text-base text-ink">
          <time dateTime={trace.created_at}>{formatDate(trace.created_at)}</time>
        </p>
      </Block>
    </div>
  );
}
