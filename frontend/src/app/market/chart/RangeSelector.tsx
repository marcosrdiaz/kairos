import { useMemo, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import { chipDate, pointDate, type ChartRow } from "./chartFormat";

interface RangeSelectorProps {
  rows: ChartRow[];
  start: number;
  end: number;
  onChange: (start: number, end: number) => void;
}

type Drag = { mode: "start" | "end" | "pan"; from: number; start: number; end: number };

/** Silueta de toda la serie (solo geometría, en un lienzo de 100 × 40). */
function sparkline(rows: ChartRow[]): string {
  if (rows.length < 2) return "";
  const values = rows.map((r) => r.value);
  const min = Math.min(...values);
  const span = Math.max(...values) - min || 1;
  const points = rows.map((r, i) => `${(i / (rows.length - 1)) * 100},${38 - ((r.value - min) / span) * 32}`);
  return `M${points.join(" L")}`;
}

/**
 * Escala de tiempo (T2-18): minigráfica de todo el periodo con una ventana dorada que marca el
 * rango que se ve arriba. Se arrastran los tiradores (cambian el inicio o el fin) o la ventana
 * entera (la desplaza). Cada tirador es un `slider` con su fecha: flechas (un día), RePág/AvPág
 * (un 10 %), Inicio/Fin. Objetivos táctiles de 44 px.
 */
export function RangeSelector({ rows, start, end, onChange }: RangeSelectorProps) {
  const track = useRef<HTMLDivElement>(null);
  const drag = useRef<Drag | null>(null);
  const [dragging, setDragging] = useState<Drag["mode"] | null>(null);
  const path = useMemo(() => sparkline(rows), [rows]);
  const last = rows.length - 1;
  const pct = (i: number) => (last > 0 ? (i / last) * 100 : 0);
  const clamp = (i: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, i));

  const indexAt = (clientX: number): number => {
    const rect = track.current?.getBoundingClientRect();
    if (!rect || rect.width === 0) return 0;
    return clamp(Math.round(((clientX - rect.left) / rect.width) * last), 0, last);
  };

  const move = (mode: Drag["mode"], to: number, base = { start, end }) => {
    if (mode === "start") onChange(clamp(to, 0, base.end - 1), base.end);
    else if (mode === "end") onChange(base.start, clamp(to, base.start + 1, last));
    else {
      const width = base.end - base.start;
      const s = clamp(to, 0, last - width);
      onChange(s, s + width);
    }
  };

  const onPointerDown = (e: PointerEvent<HTMLDivElement>) => {
    const part = (e.target as HTMLElement).closest<HTMLElement>("[data-part]")?.dataset.part;
    const at = indexAt(e.clientX);
    let mode: Drag["mode"];
    if (part === "start" || part === "end" || part === "pan") mode = part;
    else mode = Math.abs(at - start) <= Math.abs(at - end) ? "start" : "end"; // toque en la sombra
    if (mode !== "pan") move(mode, at);
    drag.current = { mode, from: at, start, end };
    setDragging(mode);
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  // Al arrastrar, como mucho un cambio por fotograma: la gráfica se redibuja a 60 fps, no por evento.
  const frame = useRef<number | null>(null);
  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    if (!d) return;
    const x = e.clientX;
    if (frame.current !== null) cancelAnimationFrame(frame.current);
    frame.current = requestAnimationFrame(() => {
      frame.current = null;
      const at = indexAt(x);
      move(d.mode, d.mode === "pan" ? d.start + (at - d.from) : at, d);
    });
  };

  const stop = () => {
    drag.current = null;
    setDragging(null);
  };

  const onKey = (mode: "start" | "end") => (e: KeyboardEvent<HTMLButtonElement>) => {
    const current = mode === "start" ? start : end;
    const page = Math.max(1, Math.round(rows.length / 10));
    const steps: Record<string, number> = {
      ArrowLeft: current - 1,
      ArrowDown: current - 1,
      ArrowRight: current + 1,
      ArrowUp: current + 1,
      PageDown: current - page,
      PageUp: current + page,
      Home: 0,
      End: last,
    };
    const to = steps[e.key];
    if (to === undefined) return;
    e.preventDefault();
    move(mode, to);
  };

  const handle = (mode: "start" | "end", index: number) => {
    const row = rows[index];
    // La fecha del inicio se abre hacia la izquierda y la del fin hacia la derecha (no se pisan),
    // salvo pegadas al borde, donde se abren hacia dentro para no salirse.
    const at = pct(index);
    const opensLeft = mode === "start" ? at > 12 : at > 88;
    return (
      <button
        type="button"
        role="slider"
        data-part={mode}
        data-dragging={dragging === mode ? "" : undefined}
        aria-label={mode === "start" ? "Inicio del rango visible" : "Fin del rango visible"}
        aria-valuemin={0}
        aria-valuemax={last}
        aria-valuenow={index}
        aria-valuetext={row ? pointDate(row.date) : undefined}
        onKeyDown={onKey(mode)}
        className="kchart-range-handle"
        style={{ left: `${pct(index)}%` }}
      >
        {row && (
          <span
            className="kchart-range-chip"
            style={{ left: "50%", translate: opensLeft ? "-88% 0" : "-12% 0" }}
            aria-hidden="true"
          >
            {chipDate(row.date)}
          </span>
        )}
      </button>
    );
  };

  return (
    <div className="px-5 pt-7 sm:px-6">
      <div
        ref={track}
        className="kchart-range-track"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={stop}
        onPointerCancel={stop}
      >
        <svg viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true" className="absolute inset-0 h-full w-full rounded-[14px]">
          <path d={`${path} L100,40 L0,40 Z`} fill="var(--kairos-color-text-muted)" opacity={0.08} />
          <path d={path} fill="none" stroke="var(--kairos-color-text-muted)" strokeWidth={1.25} opacity={0.7} vectorEffect="non-scaling-stroke" />
        </svg>
        <div className="kchart-range-shade left-0 rounded-l-[14px]" style={{ width: `${pct(start)}%` }} />
        <div className="kchart-range-shade right-0 rounded-r-[14px]" style={{ width: `${100 - pct(end)}%` }} />
        <div
          data-part="pan"
          aria-hidden="true"
          className="kchart-range-window"
          style={{ left: `${pct(start)}%`, width: `${pct(end) - pct(start)}%` }}
        />
        {handle("start", start)}
        {handle("end", end)}
      </div>
    </div>
  );
}
