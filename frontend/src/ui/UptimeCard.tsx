/*
 * Tarjeta de estado por fuente: una fila de barras diarias por servicio. Adaptada de «Uptime
 * Card» (`uptime-card.tsx`) de Kokonut UI (https://github.com/KokonutUI/kokonutui, MIT).
 * Cambios: tres estados con palabra y sin rojo («Al día», «Con retraso», «Sin datos»), sin la
 * física de ensanchado de barras ni el registro de incidencias, y la lectura del día bajo el
 * puntero va en una línea de texto, no en una ventana flotante.
 */
import { useState, type PointerEvent } from "react";
import { cn } from "../lib/cn";

export type DayState = "ok" | "late" | "none";

export interface SourceStatus {
  name: string;
  /** Un estado por día, del más antiguo al más reciente. */
  days: readonly DayState[];
}

export interface UptimeCardProps {
  title: string;
  sources: readonly SourceStatus[];
  className?: string;
}

const WORD: Record<DayState, string> = { ok: "Al día", late: "Con retraso", none: "Sin datos" };
const BAR: Record<DayState, string> = { ok: "bg-tranquilo-solid", late: "bg-atento-solid", none: "bg-nodata-bg" };

function dayLabel(index: number, count: number): string {
  const ago = count - 1 - index;
  return ago === 0 ? "Hoy" : ago === 1 ? "Ayer" : `Hace ${ago} días`;
}

function summary(source: SourceStatus): string {
  const count = (state: DayState) => source.days.filter((d) => d === state).length;
  return `${source.name}: ${count("ok")} días al día, ${count("late")} con retraso, ${count("none")} sin datos`;
}

function SourceRow({ source }: { source: SourceStatus }) {
  const [active, setActive] = useState<number | null>(null);
  const total = source.days.length;

  function move(event: PointerEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    if (rect.width === 0 || total === 0) return;
    const ratio = (event.clientX - rect.left) / rect.width;
    setActive(Math.min(total - 1, Math.max(0, Math.floor(ratio * total))));
  }

  const state = active === null ? undefined : source.days[active];
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <p className="m-0 text-base font-medium text-ink">{source.name}</p>
        <p aria-live="polite" className="m-0 text-sm text-ink-muted">
          {active !== null && state ? `${dayLabel(active, total)} · ${WORD[state]}` : " "}
        </p>
      </div>
      <div
        role="img"
        aria-label={summary(source)}
        onPointerMove={move}
        onPointerLeave={() => setActive(null)}
        className="flex h-11 touch-pan-y items-stretch gap-px"
      >
        {source.days.map((day, i) => (
          <span
            key={i}
            className={cn(
              "min-w-0 flex-1 rounded-sm transition-opacity",
              BAR[day],
              active !== null && active !== i && "opacity-50",
            )}
          />
        ))}
      </div>
    </div>
  );
}

export function UptimeCard({ title, sources, className }: UptimeCardProps) {
  return (
    <section className={cn("rounded-card border border-line bg-surface p-5", className)}>
      <h3 className="m-0 mb-4 text-xl font-semibold text-ink">{title}</h3>
      <div className="grid gap-5">
        {sources.map((source) => (
          <SourceRow key={source.name} source={source} />
        ))}
      </div>
      <ul className="m-0 mt-4 flex list-none flex-wrap gap-x-4 gap-y-1 p-0 text-sm text-ink-muted">
        {(Object.keys(WORD) as DayState[]).map((state) => (
          <li key={state} className="flex items-center gap-2">
            <span aria-hidden="true" className={cn("size-3 rounded-sm", BAR[state])} />
            {WORD[state]}
          </li>
        ))}
      </ul>
    </section>
  );
}
