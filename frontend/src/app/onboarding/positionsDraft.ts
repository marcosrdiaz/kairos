import type { AssetOut, PositionInitLine } from "../../api/generated/schema";
import { dateInputToIso, parseDecimalInput } from "./decimalInput";

/** Una fila del formulario de alta tal como la escribe el usuario. */
export interface DraftLine {
  key: number;
  asset: AssetOut | null;
  units: string;
  cost: string;
  /** "" = hoy (el backend usa `clock.now()`). */
  date: string;
}

export interface LineErrors {
  asset?: string;
  units?: string;
  cost?: string;
  date?: string;
}

export type DraftResult =
  | { ok: true; positions: PositionInitLine[] }
  | { ok: false; errors: LineErrors[]; count: number };

let nextKey = 1;
export function emptyLine(): DraftLine {
  return { key: nextKey++, asset: null, units: "", cost: "", date: "" };
}

/**
 * Valida las filas y construye el cuerpo de `POST /portfolios/{id}/positions`.
 * `today` es "AAAA-MM-DD" (lo da quien llama, para que la función sea pura).
 */
export function buildPositions(lines: DraftLine[], today: string): DraftResult {
  const errors: LineErrors[] = [];
  const positions: PositionInitLine[] = [];
  let count = 0;
  for (const line of lines) {
    const e: LineErrors = {};
    if (!line.asset) e.asset = "Elige un activo de la lista.";
    const units = parseDecimalInput(line.units, 8);
    if (!units.ok) e.units = units.error;
    const cost = parseDecimalInput(line.cost, 2);
    if (!cost.ok) e.cost = cost.error;
    if (line.date && line.date > today) e.date = "La fecha de compra no puede ser futura.";
    errors.push(e);
    count += Object.keys(e).length;
    if (line.asset && units.ok && cost.ok && !e.date) {
      const p: PositionInitLine = {
        asset_id: line.asset.id,
        units: units.value,
        avg_cost_eur: cost.value,
      };
      if (line.date) p.acquired_at = dateInputToIso(line.date);
      positions.push(p);
    }
  }
  return count > 0 ? { ok: false, errors, count } : { ok: true, positions };
}

/** Hoy en la zona de Madrid como "AAAA-MM-DD" (el `max` de los <input type="date">). */
export function todayInMadrid(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Madrid" }).format(now);
}
