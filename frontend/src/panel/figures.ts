import { formatEur } from "../lib/format";

/** Importe con signo explícito ("+90,00 €" / "-514,00 €"): el signo no depende del color. */
export function signedEur(value: string, digits = 2): string {
  const v = value.trim();
  const isZero = /^[+-]?0*(\.0*)?$/.test(v);
  const text = formatEur(v, digits);
  return v.startsWith("-") || isZero ? text : `+${text}`;
}
