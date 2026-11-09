import { formatEur, formatEurRange } from "../lib/format";

/** Importe con signo explícito ("+90,00 €" / "-514,00 €"): el signo no depende del color. */
export function signedEur(value: string, digits = 2): string {
  const v = value.trim();
  const isZero = /^[+-]?0*(\.0*)?$/.test(v);
  const text = formatEur(v, digits);
  return v.startsWith("-") || isZero ? text : `+${text}`;
}

/**
 * Impacto estimado como rango: "entre -10 € y 190 €". Si los dos extremos salen iguales una vez
 * redondeados (el motor no ha podido estimar incertidumbre), "entre X y X" sería absurdo: se
 * muestra "≈ X". Sigue siendo una estimación, nunca una cifra exacta.
 */
export function impactRange(low: string, high: string): string {
  const lo = formatEur(low, 0);
  const hi = formatEur(high, 0);
  return lo === hi ? `≈ ${lo}` : formatEurRange(low, high);
}
