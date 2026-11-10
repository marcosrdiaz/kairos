import { ApiError } from "../../api/client";
import type { PortfolioKind, RiskProfile } from "../../api/generated/schema";

export const KIND_OPTIONS: { value: PortfolioKind; label: string; hint: string }[] = [
  { value: "personal", label: "Personal", hint: "Tus ahorros e inversiones" },
  { value: "business", label: "Negocio", hint: "La tesorería de tu empresa o actividad" },
  { value: "family", label: "Familia", hint: "Por ejemplo, la de tus hijos" },
  { value: "other", label: "Otra", hint: "Cualquier otro fin" },
];

export const RISK_OPTIONS: { value: RiskProfile; label: string; hint: string }[] = [
  { value: "conservador", label: "Conservador", hint: "Priorizas no perder" },
  { value: "moderado", label: "Moderado", hint: "Aceptas altibajos a medio plazo" },
  { value: "agresivo", label: "Agresivo", hint: "Aceptas caídas fuertes a largo plazo" },
];

export type Method = "manual" | "csv";

export interface DetailsDraft {
  name: string;
  kind: PortfolioKind;
  risk: RiskProfile | null;
  method: Method;
  file: File | null;
}

export type DetailsErrors = Partial<Record<"name" | "risk" | "file", string>>;

/** Límites del contrato (`PortfolioName` y `IMPORT_CSV_MAX_CHARS` en `schemas/portfolio_manage.py`). */
export const NAME_MAX = 60;
export const CSV_MAX_CHARS = 200_000;

/** Comprueba el paso 1 en el navegador. Devuelve los errores por campo (vacío si está bien). */
export function validateDetails(d: DetailsDraft): DetailsErrors {
  const errors: DetailsErrors = {};
  const name = d.name.trim();
  if (!name) errors.name = "Ponle un nombre a la cartera.";
  else if (name.length > NAME_MAX) errors.name = `El nombre no puede pasar de ${NAME_MAX} caracteres.`;
  if (!d.risk) errors.risk = "Elige un perfil de riesgo.";
  if (d.method === "csv" && !d.file) errors.file = "Elige el fichero CSV con tus posiciones.";
  return errors;
}

/** Un error de una fila del CSV (`ImportRowError` del backend, en `details.rows`). */
export interface ImportRowError {
  line: number;
  field: string | null;
  code: string;
  message: string;
}

function isRowError(v: unknown): v is ImportRowError {
  if (typeof v !== "object" || v === null) return false;
  const r = v as Record<string, unknown>;
  return typeof r.line === "number" && typeof r.message === "string";
}

/** Filas con error de un 422 de `/portfolios/import`, o [] si el error es de otro tipo. */
export function importRowErrors(error: unknown): ImportRowError[] {
  if (!(error instanceof ApiError)) return [];
  const rows = error.details.rows;
  return Array.isArray(rows) ? rows.filter(isRowError) : [];
}

/** Mensaje general cuando falla crear o importar (los errores por fila se listan aparte). */
export function createErrorText(error: unknown): string {
  if (importRowErrors(error).length > 0) {
    return "El fichero tiene filas por revisar. No se ha creado la cartera.";
  }
  if (error instanceof ApiError && error.status === 422) {
    return "Algún dato no es válido. Revísalo y vuelve a intentarlo.";
  }
  return "No hemos podido crear la cartera. Vuelve a intentarlo en unos segundos.";
}
