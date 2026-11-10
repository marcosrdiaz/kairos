import { useId, useState } from "react";
import { DOWN, DOWN_BG, INFO, REFERENCE, UP } from "./colors";

/** Muestra de línea (trazo) o de punto, decorativa: el significado lo da el texto. */
function Swatch({ kind, color }: { kind: "line" | "dash" | "dot" | "area" | "news"; color: string }) {
  return (
    <svg viewBox="0 0 28 14" className="h-3.5 w-7 shrink-0" aria-hidden="true">
      {kind === "line" && <path d="M1 10 C 8 2, 14 12, 27 4" fill="none" stroke={color} strokeWidth={2.5} strokeLinecap="round" />}
      {kind === "dash" && <path d="M1 7 H27" stroke={color} strokeWidth={1.5} strokeDasharray="5 4" />}
      {kind === "dot" && <circle cx={14} cy={7} r={5} fill={color} />}
      {kind === "news" && <circle cx={14} cy={7} r={5.5} fill="var(--kairos-color-surface)" stroke={color} strokeWidth={1.8} />}
      {kind === "area" && (
        <>
          <rect x={1} y={1} width={26} height={6} fill={UP} opacity={0.3} />
          <rect x={1} y={7} width={26} height={6} fill={DOWN_BG} />
          <path d="M1 7 H27" stroke={REFERENCE} strokeWidth={1.2} strokeDasharray="3 3" />
        </>
      )}
    </svg>
  );
}

const ITEMS = [
  { kind: "line", color: UP, label: "Por encima del valor inicial", text: "la cartera vale más que al empezar el periodo." },
  { kind: "line", color: DOWN, label: "Por debajo del valor inicial", text: "vale menos que al empezar." },
  { kind: "dash", color: REFERENCE, label: "Línea dorada", text: "el valor al empezar el periodo: la referencia para ganar o perder." },
  { kind: "area", color: UP, label: "Zonas sombreadas", text: "la distancia a esa referencia: verde si se gana, granate si se pierde." },
  { kind: "dot", color: INFO, label: "Punto azul", text: "ese día entró o salió dinero (compra, aportación o venta): un salto ahí no es rentabilidad." },
  { kind: "news", color: REFERENCE, label: "Círculo con icono", text: "una noticia que afectó a tu cartera, en su fecha real. Pasa el ratón o llega con Tab para ver qué pasó, cómo se movió el mercado y su impacto estimado." },
] as const;

/** Icono de información con el aro que gira a «cerrar» al abrir la leyenda (decorativo). */
function LegendIcon({ open }: { open: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className="size-5 shrink-0" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      {open ? <path d="m8.5 13.5 3.5-3.5 3.5 3.5" /> : <path d="M12 11v5M12 8h.01" />}
    </svg>
  );
}

/**
 * Leyenda que explica cómo leer la gráfica entera (colores, referencia, zonas y aportaciones).
 * Plegada por defecto tras un botón «Mostrar leyenda» (`aria-expanded`), para que la atención
 * vaya a la gráfica. Lista de texto: no depende del color y el lector la lee como lista.
 */
export function ChartLegend() {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <div className="px-5 sm:px-6">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((o) => !o)}
        className="inline-flex min-h-touch cursor-pointer items-center gap-2 rounded-full border-0 bg-transparent px-1 text-sm font-semibold text-accent hover:underline"
      >
        <LegendIcon open={open} />
        {open ? "Ocultar leyenda" : "Mostrar leyenda"}
      </button>
      <div id={id} hidden={!open} className="pb-1 pt-2">
        <h3 className="m-0 mb-2 text-sm font-semibold text-ink">Cómo leer la gráfica</h3>
        <LegendList />
      </div>
    </div>
  );
}

function LegendList() {
  return (
      <ul className="m-0 grid list-none gap-x-6 gap-y-2 p-0 text-sm text-ink-muted md:grid-cols-2">
        {ITEMS.map((item) => (
          <li key={item.label} className="flex items-start gap-2.5">
            <span className="mt-1">
              <Swatch kind={item.kind} color={item.color} />
            </span>
            <span>
              <span className="font-semibold text-ink">{item.label}:</span> {item.text}
            </span>
          </li>
        ))}
        <li className="flex items-start gap-2.5 md:col-span-2">
          <span className="mt-0.5 w-7 shrink-0 text-center text-ink" aria-hidden="true">
            ⇔
          </span>
          <span>
            <span className="font-semibold text-ink">Escala de fechas:</span> arrastra la ventana o sus bordes
            para acercar un tramo; con el teclado, flechas en cada borde. Pasa el ratón o las flechas por la
            línea para ver el valor y la variación de cada día.
          </span>
        </li>
      </ul>
  );
}
