import { useId } from "react";
import { kindSuffix } from "./kindLabel";
import { usePortfolioId } from "./usePortfolioId";
import { usePortfolios } from "./usePortfolios";
import { useSyncPortfolioId } from "./useSyncPortfolioId";

interface PortfolioPickerProps {
  /** Sin leyenda visible (barra lateral). La leyenda sigue para el lector de pantalla. */
  compact?: boolean;
}

/**
 * Selector de cartera (T1-19, T4-13) como grupo de radios nativos: flechas para moverse, el
 * lector anuncia "Cartera, grupo, Negocio, botón de opción, 2 de 3". Cada opción lleva el
 * nombre y, si añade algo, el tipo. La elegida va en `?p=` y se recuerda en el navegador.
 * La opción marcada cambia de relleno, no solo de color de texto.
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
        className="h-[3.25rem] w-44 animate-pulse rounded-full bg-surface-muted motion-reduce:animate-none"
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

  return (
    <fieldset className="m-0 min-w-0 border-0 p-0">
      <legend className={compact ? "sr-only" : "mb-2 p-0 text-base font-semibold text-ink"}>
        Cartera
      </legend>
      <div className="inline-flex max-w-full flex-wrap gap-1 rounded-[1.75rem] border border-line-strong bg-surface p-1">
        {data.map((p) => {
          const kind = kindSuffix(p);
          return (
            <label key={p.id} className="relative flex min-w-0">
              <input
                type="radio"
                name={name}
                value={p.id}
                checked={p.id === current}
                onChange={() => select(p.id)}
                className="peer sr-only"
              />
              <span
                className={[
                  "flex min-h-touch min-w-0 cursor-pointer items-baseline gap-1.5 self-stretch rounded-full px-5 py-2.5 text-base font-medium text-ink-muted transition-colors",
                  "peer-checked:bg-accent peer-checked:font-semibold peer-checked:text-on-accent",
                  "peer-[:not(:checked)]:hover:bg-surface-muted peer-[:not(:checked)]:hover:text-ink",
                  "peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-focus",
                ].join(" ")}
              >
                <span className="truncate">{p.name}</span>
                {kind && !compact && (
                  <span aria-hidden="true" className="text-sm font-normal">
                    · {kind}
                  </span>
                )}
                {kind && <span className="sr-only">, {kind}</span>}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
