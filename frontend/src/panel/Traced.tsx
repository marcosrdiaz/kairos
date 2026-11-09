import type { ReactNode } from "react";
import { TraceFigure } from "../components/trace/TraceFigure";

interface TracedProps {
  /** `calc_id` de la cifra; si el backend no lo da, se pinta igual. */
  calcId?: string | null | undefined;
  children: ReactNode;
}

/** Envuelve una cifra que tiene `calc_id` y la enlaza a su traza ("¿De dónde sale?", T2-11). */
export function Traced({ calcId, children }: TracedProps) {
  return <TraceFigure calcId={calcId}>{children}</TraceFigure>;
}
