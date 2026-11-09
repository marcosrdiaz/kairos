import { formatDate, formatEur, formatPercent, formatUnits } from "../../lib/format";
import { FIELD_LABEL } from "./labels";

/** Un dato de `inputs` u `outputs`, listo para pintar: texto o lista anidada. */
export type TraceField =
  | { key: string; label: string; text: string }
  | { key: string; label: string; fields: TraceField[] };

type Unit = "eur" | "percent";

const NUMERIC = /^[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?$/;
const ISO_DATE = /^\d{4}-\d{2}-\d{2}(?:T[\d:.]+(?:Z|[-+]\d{2}:?\d{2})?)?$/;
const EUR_KEY = /(?:^|_)eur(?:_|$)/;
const PERCENT_KEY = /(?:_pct|weights?|_drift)$/;
/** Claves que el backend entrega como fracción (0.76 = 76 %) sin indicarlo en el nombre. */
const PERCENT_KEYS = new Set([
  "allocation",
  "by_country",
  "by_currency",
  "by_sector",
  "current",
  "drift_equity",
  "drift_threshold",
  "equity_current",
  "equity_target",
  "returns_by_class",
  "target",
]);
/** Claves que nombran a un elemento de una lista, por orden de preferencia. */
const ITEM_NAME_KEYS = ["asset_id", "company", "event_id", "id", "rule", "title"];

function unitOf(key: string): Unit | undefined {
  if (EUR_KEY.test(key)) return "eur";
  if (PERCENT_KEY.test(key) || PERCENT_KEYS.has(key)) return "percent";
  return undefined;
}

function isPrimitive(value: unknown): boolean {
  return value === null || typeof value !== "object";
}

/** Los importes llegan como string Decimal: se formatean sin pasar por `number`. */
function formatPrimitive(value: unknown, unit: Unit | undefined): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Sí" : "No";
  const text = String(value);
  if (NUMERIC.test(text)) {
    if (unit === "eur") return formatEur(text);
    if (unit === "percent") return formatPercent(text);
    return formatUnits(text, 8);
  }
  return ISO_DATE.test(text) ? formatDate(text) : text;
}

function itemName(item: unknown, position: number): string {
  if (item !== null && typeof item === "object") {
    const record = item as Record<string, unknown>;
    const name = ITEM_NAME_KEYS.map((key) => record[key]).find((v) => typeof v === "string");
    if (typeof name === "string") return name;
  }
  return String(position);
}

function toField(key: string, label: string, value: unknown, unit: Unit | undefined): TraceField {
  if (Array.isArray(value)) {
    if (value.length === 0) return { key, label, text: "—" };
    if (value.every(isPrimitive)) {
      return { key, label, text: value.map((v) => formatPrimitive(v, unit)).join(", ") };
    }
    const fields = value.map((item, i) => {
      const name = itemName(item, i + 1);
      return toField(`${key}.${i}`, name, item, unit);
    });
    return { key, label, fields };
  }
  if (value !== null && typeof value === "object") {
    const fields = toTraceFields(value as Record<string, unknown>, unit);
    return fields.length > 0 ? { key, label, fields } : { key, label, text: "—" };
  }
  return { key, label, text: formatPrimitive(value, unit) };
}

/**
 * Convierte `inputs` u `outputs` en campos con nombre en español y formato de cifra por clave
 * (`*_eur` en euros, `*_pct` y pesos en porcentaje). Una clave hija sin unidad propia hereda la
 * de su padre: en `{"value_eur": {"IE00…": "10.50"}}`, el importe del activo también va en euros.
 */
export function toTraceFields(record: Record<string, unknown>, inherited?: Unit): TraceField[] {
  return Object.entries(record).map(([key, value]) =>
    toField(key, FIELD_LABEL[key] ?? key, value, unitOf(key) ?? inherited),
  );
}
