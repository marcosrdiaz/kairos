/**
 * Formateo de números: único punto de entrada para mostrar cifras.
 *
 * Los importes llegan del backend como string Decimal ("1234.50"). Aquí NO se
 * convierten a number: Intl.NumberFormat.format acepta strings decimales y los
 * formatea sin pasar por coma flotante. Redondeo half-even solo al presentar.
 */
const LOCALE = "es-ES";

export type DecimalString = string;

// Intl acepta strings numéricos exactos; TS los tipa como plantilla.
const dec = (v: DecimalString) => v as `${number}`;

const eurFormatters = new Map<number, Intl.NumberFormat>();

/** "1234.5" -> "1234,50 €" (es-ES no agrupa miles en números de 4 cifras). */
export function formatEur(value: DecimalString, digits = 2): string {
  let f = eurFormatters.get(digits);
  if (!f) {
    f = new Intl.NumberFormat(LOCALE, {
      style: "currency",
      currency: "EUR",
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
      roundingMode: "halfEven",
    });
    eurFormatters.set(digits, f);
  }
  return f.format(dec(value));
}

/** Rango de impacto: "entre -640 € y -380 €" (rangos, no cifras exactas). */
export function formatEurRange(low: DecimalString, high: DecimalString): string {
  return `entre ${formatEur(low, 0)} y ${formatEur(high, 0)}`;
}

const percent = new Intl.NumberFormat(LOCALE, {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  roundingMode: "halfEven",
});

/** Fracción decimal ("0.0123") -> "1,2 %". */
export function formatPercent(fraction: DecimalString): string {
  return percent.format(dec(fraction));
}

const units = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 0,
  maximumFractionDigits: 4,
  roundingMode: "halfEven",
});

/** Participaciones: "12.5" -> "12,5". */
export function formatUnits(value: DecimalString): string {
  return units.format(dec(value));
}

const dateFmt = new Intl.DateTimeFormat(LOCALE, {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "Europe/Madrid",
});

/** ISO 8601 con zona -> "8 de noviembre de 2026" (hora de Madrid). */
export function formatDate(iso: string): string {
  return dateFmt.format(new Date(iso));
}
