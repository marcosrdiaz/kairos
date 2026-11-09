/**
 * Lectura de cifras escritas por el usuario. Devuelve un string Decimal con punto ("1234.56"),
 * nunca un `number`: participaciones e importes no pasan por coma flotante (CLAUDE.md).
 *
 * Acepta coma o punto como separador decimal y NO acepta separador de miles: en es-ES
 * "1.234" puede ser mil doscientos o uno con dos, y con dinero no se adivina.
 */
export type DecimalParse = { ok: true; value: string } | { ok: false; error: string };

const SHAPE = /^\d+(?:[.,]\d+)?$/;

export function parseDecimalInput(raw: string, maxDecimals: number): DecimalParse {
  const text = raw.replace(/\s/g, "");
  if (text === "") return { ok: false, error: "Escribe una cifra." };
  if (!SHAPE.test(text)) {
    return /^\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?$/.test(text) && /[.,].*[.,]/.test(text)
      ? { ok: false, error: "Escríbela sin separador de miles, por ejemplo 1234,56." }
      : { ok: false, error: "Escribe solo números, con coma para los decimales." };
  }
  const [intPart = "", decPart = ""] = text.replace(",", ".").split(".");
  if (decPart.length > maxDecimals) {
    return {
      ok: false,
      error:
        maxDecimals === 2
          ? "Como mucho 2 decimales (céntimos)."
          : `Como mucho ${maxDecimals} decimales.`,
    };
  }
  const int = intPart.replace(/^0+(?=\d)/, "");
  if (/^0*$/.test(int) && /^0*$/.test(decPart)) {
    return { ok: false, error: "Tiene que ser mayor que cero." };
  }
  return { ok: true, value: decPart ? `${int}.${decPart}` : int };
}

/** Fecha de un <input type="date"> ("2024-03-06") a ISO UTC al inicio del día. */
export function dateInputToIso(value: string): string {
  return `${value}T00:00:00Z`;
}
