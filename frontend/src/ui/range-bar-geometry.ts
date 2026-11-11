/*
 * Geometría de `RangeBar` (T5-07): convierte los extremos y el centro de un rango en fracciones
 * del carril. Solo dibujo: estas posiciones nunca se muestran como cifra.
 *
 * El carril va siempre del rango al cero, así que el cero se ve en todas las barras: un rango
 * estrecho y lejos del cero se lee como «seguro que en contra (o a favor), y poco», y uno que lo
 * cruza, como «puede ir en los dos sentidos».
 */

export interface RangeBarLayout {
  /** Fracciones del carril, de 0 a 1. */
  start: number;
  end: number;
  center: number;
  zero: number;
}

/** Margen a cada lado del carril, en fracción de su ancho. */
const PAD = 0.05;

/**
 * Coloca el tramo `[low, high]` y el cero en el carril. Sin rango (extremos iguales o no
 * numéricos) devuelve `null`: no hay nada que dibujar.
 */
export function rangeBarLayout(low: number, high: number, center: number): RangeBarLayout | null {
  if (![low, high, center].every(Number.isFinite)) return null;
  const lo = Math.min(low, high);
  const hi = Math.max(low, high);
  if (hi - lo <= 0) return null;
  const from = Math.min(lo, 0);
  const to = Math.max(hi, 0);
  const pad = (to - from) * PAD;
  const min = from - pad;
  const max = to + pad;
  const at = (x: number) => (x - min) / (max - min);
  return {
    start: at(lo),
    end: at(hi),
    center: at(Math.min(hi, Math.max(lo, center))),
    zero: at(0),
  };
}
