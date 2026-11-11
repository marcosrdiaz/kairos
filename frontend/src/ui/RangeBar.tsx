/*
 * Barra de rango de un impacto estimado (T5-07): el tramo entre los dos extremos, una marca en el
 * centro y la línea del cero, que siempre está en el carril (ver `range-bar-geometry.ts`).
 * Propia, sin código de terceros.
 *
 * Las posiciones son solo dibujo: convierten los importes en fracciones del carril y nunca se
 * muestran. La lectura (con las cifras formateadas por `lib/format.ts`) llega hecha en `label` y
 * va en el `aria-label`: la barra no añade texto visible. La confianza solo cambia la opacidad
 * del tramo; quien la usa debe decirla también con palabras.
 */
import { cn } from "../lib/cn";
import { rangeBarLayout } from "./range-bar-geometry";

type RangeBarConfidence = "alta" | "media" | "baja";

const OPACITY: Record<RangeBarConfidence, number> = { alta: 1, media: 0.7, baja: 0.45 };

export interface RangeBarProps {
  low: number;
  high: number;
  center: number;
  /** Lectura completa para el lector de pantalla (p. ej. «entre X € y Y €, centro ≈ Z €»). */
  label: string;
  confidence?: RangeBarConfidence;
  className?: string;
}

const pct = (f: number) => `${f * 100}%`;

export function RangeBar({ low, high, center, label, confidence = "alta", className }: RangeBarProps) {
  const layout = rangeBarLayout(low, high, center);
  if (!layout) return null;
  return (
    <div
      role="img"
      aria-label={label}
      className={cn("relative h-5 w-full max-w-sm", className)}
    >
      <span
        aria-hidden="true"
        className="absolute inset-x-0 top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-line"
      />
      <span
        aria-hidden="true"
        data-slot="range-bar-fill"
        style={{
          left: pct(layout.start),
          width: pct(layout.end - layout.start),
          opacity: OPACITY[confidence],
        }}
        className="absolute top-1/2 h-1.5 min-w-1.5 -translate-y-1/2 rounded-full bg-ink-muted forced-colors:bg-[CanvasText]"
      />
      <span
        aria-hidden="true"
        data-slot="range-bar-zero"
        style={{ left: pct(layout.zero) }}
        className="absolute inset-y-0 w-0.5 -translate-x-1/2 rounded-full bg-line-strong forced-colors:bg-[GrayText]"
      />
      <span
        aria-hidden="true"
        data-slot="range-bar-center"
        style={{ left: pct(layout.center) }}
        className="absolute top-1/2 h-4 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ink ring-2 ring-surface forced-colors:bg-[CanvasText]"
      />
    </div>
  );
}
