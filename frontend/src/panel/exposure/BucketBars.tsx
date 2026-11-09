import type { CSSProperties } from "react";
import type { ExposureBucket } from "../../api/generated/schema";
import { formatEur, formatPercent } from "../../lib/format";
import { Traced } from "../Traced";

/** Cubos que el backend agrupa como "resto": van al final y con la barra más tenue. */
const REST_KEYS = new Set(["OTHER", "other"]);
const VISIBLE = 6;

function Row({ bucket, calcId }: { bucket: ExposureBucket; calcId: string }) {
  const rest = REST_KEYS.has(bucket.key);
  return (
    <li className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1">
      <span className={`text-base ${rest ? "text-ink-muted" : "text-ink"}`}>{bucket.label}</span>
      <span className="text-right text-base tabular-nums text-ink">
        <Traced calcId={calcId}>{formatPercent(bucket.weight)}</Traced>
        <span className="ml-2 text-sm text-ink-muted">{formatEur(bucket.value_eur, 0)}</span>
      </span>
      {/* Barra: el ancho sale de la fracción tal cual (calc), sin pasarla a number. */}
      <span aria-hidden="true" className="col-span-2 block h-2 rounded-full bg-surface-muted">
        <span
          className={`block h-full rounded-full ${rest ? "bg-line" : "bg-line-strong"}`}
          style={{ width: `calc(${bucket.weight} * 100%)` } as CSSProperties}
        />
      </span>
    </li>
  );
}

/** Reparto por país, sector o divisa. Los primeros 6 a la vista; el resto, plegado. */
export function BucketBars({
  title,
  buckets,
  calcId,
}: {
  title: string;
  buckets: ExposureBucket[];
  calcId: string;
}) {
  const sorted = [...buckets].sort(
    (a, b) => Number(REST_KEYS.has(a.key)) - Number(REST_KEYS.has(b.key)),
  );
  const main = sorted.slice(0, VISIBLE);
  const more = sorted.slice(VISIBLE);
  return (
    <section aria-label={title} className="rounded-card border border-line bg-surface p-6">
      <h3 className="m-0 text-lg font-semibold text-ink">{title}</h3>
      <ul className="m-0 mt-4 flex list-none flex-col gap-3 p-0">
        {main.map((b) => (
          <Row key={b.key} bucket={b} calcId={calcId} />
        ))}
      </ul>
      {more.length > 0 && (
        <details className="mt-3">
          <summary className="inline-flex min-h-touch cursor-pointer items-center font-semibold text-accent underline">
            Ver {more.length} más
          </summary>
          <ul className="m-0 mt-2 flex list-none flex-col gap-3 p-0">
            {more.map((b) => (
              <Row key={b.key} bucket={b} calcId={calcId} />
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
