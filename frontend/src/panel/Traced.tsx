import type { ReactNode } from "react";

interface TracedProps {
  /** `calc_id` de la cifra; si el backend no lo da, se pinta igual. */
  calcId?: string | null | undefined;
  children: ReactNode;
}

/**
 * Envuelve una cifra que tiene `calc_id`. Hoy solo la marca (`data-calc-id`) y no cambia nada
 * en pantalla. T2-11 ("¿De dónde sale?") sustituirá este cuerpo por el enlace a la traza
 * (`GET /traces/{calc_id}`); las pantallas del panel no tendrán que tocarse.
 */
export function Traced({ calcId, children }: TracedProps) {
  return <span data-calc-id={calcId ?? undefined}>{children}</span>;
}
