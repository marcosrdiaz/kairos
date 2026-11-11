import { useId } from "react";
import { cn } from "../../lib/cn";
import { initials } from "./initials";
import { kindSuffix } from "./kindLabel";
import { usePortfolioId } from "./usePortfolioId";
import { usePortfolios } from "./usePortfolios";
import { useSyncPortfolioId } from "./useSyncPortfolioId";

interface PortfolioPickerProps {
  /** Sin leyenda visible (barra lateral). La leyenda sigue para el lector de pantalla. */
  compact?: boolean;
}

/** Colores de los círculos, por orden de la lista (fondo y letra con contraste AA en claro y oscuro). */
const AVATAR_TONES = [
  "bg-icon-blue-bg text-icon-blue",
  "bg-icon-gold-bg text-icon-gold",
  "bg-icon-green-bg text-icon-green",
  "bg-icon-purple-bg text-icon-purple",
  "bg-icon-red-bg text-icon-red",
] as const;

// Agrupados (se solapan) hasta que el grupo recibe el ratón o el foco; en pantallas táctiles,
// siempre separados: la selección nunca depende del hover.
const SPREAD =
  "group-hover/picker:ml-2 group-hover/picker:w-28 group-focus-within/picker:ml-2 group-focus-within/picker:w-28 pointer-coarse:ml-1 pointer-coarse:w-20";
const NAME_SHOWN =
  "group-hover/picker:opacity-100 group-focus-within/picker:opacity-100 pointer-coarse:opacity-100";

/**
 * Selector de cartera (T1-19, T4-13; rediseñado en T5-15) como círculos de perfil. Por dentro
 * sigue siendo un grupo de radios nativos: flechas para moverse, el lector anuncia "Cartera,
 * grupo, Negocio, botón de opción, 2 de 3". Los círculos van agrupados y se separan, con su
 * nombre, al pasar el ratón o al recibir foco. La elegida lleva anillo y marca, y su nombre
 * se ve siempre debajo («Ahora: …»). La elegida va en `?p=` y se recuerda en el navegador.
 */
export function PortfolioPicker({ compact = false }: PortfolioPickerProps) {
  const [current, select] = usePortfolioId();
  const { data, isPending, isError } = usePortfolios();
  const name = useId();
  useSyncPortfolioId();

  if (isPending) {
    return (
      <div
        aria-hidden="true"
        className="size-14 animate-pulse rounded-full bg-surface-muted motion-reduce:animate-none"
      />
    );
  }
  if (isError || data.length === 0) {
    return compact ? null : (
      <p className="m-0 text-base text-ink-muted">
        Ahora mismo no podemos cargar las carteras. Vuelve a intentarlo en unos segundos.
      </p>
    );
  }

  const selected = data.find((p) => p.id === current);
  const selectedKind = selected ? kindSuffix(selected) : "";

  return (
    <fieldset className="m-0 min-w-0 border-0 p-0">
      <legend className={compact ? "sr-only" : "mb-3 p-0 text-base font-semibold text-ink"}>
        Cartera
      </legend>
      <div className="flex flex-col gap-2">
        <div className="group/picker flex flex-wrap items-start gap-y-3">
          {data.map((p, i) => {
            const kind = kindSuffix(p);
            const checked = p.id === current;
            return (
              <label
                key={p.id}
                className={cn(
                  "relative -ml-3 flex w-14 shrink-0 cursor-pointer flex-col items-center first:ml-0",
                  "transition-[margin,width] duration-200 ease-out motion-reduce:transition-none",
                  SPREAD,
                  checked ? "z-10" : "hover:z-20",
                )}
              >
                <input
                  type="radio"
                  name={name}
                  value={p.id}
                  checked={checked}
                  onChange={() => select(p.id)}
                  className="peer sr-only"
                />
                <span
                  aria-hidden="true"
                  className={cn(
                    "flex size-14 items-center justify-center rounded-full border-2 border-surface text-lg font-semibold",
                    "transition-transform duration-150 ease-out active:scale-95 motion-reduce:transition-none",
                    "peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-focus",
                    AVATAR_TONES[i % AVATAR_TONES.length],
                    checked && "ring-3 ring-accent ring-offset-2 ring-offset-surface",
                  )}
                >
                  {initials(p.name)}
                </span>
                {checked && (
                  <span
                    aria-hidden="true"
                    className="absolute top-9 left-1/2 ml-2 flex size-6 items-center justify-center rounded-full border-2 border-surface bg-accent text-on-accent"
                  >
                    <svg
                      viewBox="0 0 12 12"
                      className="size-3"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M2.5 6.2 5 8.5l4.5-5" />
                    </svg>
                  </span>
                )}
                <span
                  className={cn(
                    "mt-1.5 w-full truncate text-center text-sm text-ink opacity-0",
                    "transition-opacity duration-200 ease-out motion-reduce:transition-none",
                    checked ? "font-semibold" : "font-medium",
                    NAME_SHOWN,
                  )}
                >
                  {p.name}
                </span>
                {kind && <span className="sr-only">, {kind}</span>}
              </label>
            );
          })}
        </div>
        {selected && !compact && (
          <p aria-hidden="true" className="m-0 text-base text-ink-muted">
            {`Ahora: ${selected.name}${selectedKind ? ` · ${selectedKind}` : ""}`}
          </p>
        )}
      </div>
    </fieldset>
  );
}
