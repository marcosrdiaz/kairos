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

const weight = new Intl.NumberFormat(LOCALE, {
  style: "percent",
  minimumFractionDigits: 0,
  maximumFractionDigits: 6,
  roundingMode: "halfEven",
});

/**
 * Peso de un reparto guardado con 8 decimales ("0.33333333") -> "33,333333 %"; "0.7" -> "70 %".
 * Sin redondear a 1 decimal: tres tercios no deben verse como un 99,9 %.
 */
export function formatWeight(fraction: DecimalString): string {
  return weight.format(dec(fraction));
}

const unitFormatters = new Map<number, Intl.NumberFormat>();

/**
 * Participaciones: "12.5" -> "12,5". Por defecto hasta 4 decimales; `maxDigits = 8` (los de
 * `NUMERIC(20,8)`) cuando la cifra exacta importa, p. ej. las disponibles para vender.
 */
export function formatUnits(value: DecimalString, maxDigits = 4): string {
  let f = unitFormatters.get(maxDigits);
  if (!f) {
    f = new Intl.NumberFormat(LOCALE, {
      minimumFractionDigits: 0,
      maximumFractionDigits: maxDigits,
      roundingMode: "halfEven",
    });
    unitFormatters.set(maxDigits, f);
  }
  return f.format(dec(value));
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

const dayMonthFmt = new Intl.DateTimeFormat(LOCALE, {
  day: "numeric",
  month: "short",
  timeZone: "Europe/Madrid",
});

/** ISO 8601 con zona -> "8 nov" (hora de Madrid), para columnas estrechas. */
export function formatDayMonth(iso: string): string {
  return dayMonthFmt.format(new Date(iso));
}
