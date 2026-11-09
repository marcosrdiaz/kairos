import type { ReactNode } from "react";
import type { TraceOut } from "../../api/generated/schema";
import { formatDate } from "../../lib/format";
import { toTraceFields, type TraceField } from "./traceFields";

function FieldList({ fields }: { fields: TraceField[] }) {
  return (
    <dl className="m-0 flex flex-col gap-2">
      {fields.map((field) => (
        <div key={field.key} className="flex flex-col">
          <dt className="text-sm text-ink-muted">{field.label}</dt>
          {"text" in field ? (
            <dd className="m-0 break-words text-base text-ink tabular-nums">{field.text}</dd>
          ) : (
            <dd className="m-0 mt-1 border-l-2 border-line pl-3">
              <FieldList fields={field.fields} />
            </dd>
          )}
        </div>
      ))}
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
        <code className="block whitespace-pre-wrap break-words rounded-control bg-surface-muted p-3 text-sm text-ink">
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
