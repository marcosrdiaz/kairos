import type { AssetOut, PositionInitLine, TransactionRequest } from "../../api/generated/schema";
import { dateInputToIso, parseDecimalInput } from "./decimalInput";

/** Una fila del formulario de alta tal como la escribe el usuario. */
export interface DraftLine {
  key: number;
  asset: AssetOut | null;
  units: string;
  /** "" = sin precio: se compra al último precio del proveedor (`POST /transactions`). */
  cost: string;
  /** "" = hoy (el backend usa `clock.now()`). Solo vale con precio. */
  date: string;
}

export interface LineErrors {
  asset?: string;
  units?: string;
  cost?: string;
  date?: string;
}

/**
 * Lo que hay que enviar: las filas con precio van juntas en un alta (`POST /positions`) y cada
 * fila sin precio es una compra por participaciones (`POST /transactions`). `*Keys` dice de qué
 * fila sale cada elemento, en el mismo orden.
 */
export interface DraftPlan {
  positions: PositionInitLine[];
  positionKeys: number[];
  buys: TransactionRequest[];
  buyKeys: number[];
}

export type DraftResult =
  | ({ ok: true } & DraftPlan)
  | { ok: false; errors: LineErrors[]; count: number };

export const DATE_NEEDS_COST = "Para indicar la fecha, indica también el precio de compra.";

let nextKey = 1;
export function emptyLine(): DraftLine {
  return { key: nextKey++, asset: null, units: "", cost: "", date: "" };
}

/**
 * Valida las filas y las reparte entre el alta con precio y las compras por participaciones.
 * `today` es "AAAA-MM-DD" (lo da quien llama, para que la función sea pura).
 */
export function buildPositions(lines: DraftLine[], today: string): DraftResult {
  const errors: LineErrors[] = [];
  const plan: DraftPlan = { positions: [], positionKeys: [], buys: [], buyKeys: [] };
  let count = 0;
  for (const line of lines) {
    const e: LineErrors = {};
    if (!line.asset) e.asset = "Elige un activo de la lista.";
    const units = parseDecimalInput(line.units, 8);
    if (!units.ok) e.units = units.error;
    const priced = line.cost.trim() !== "";
    const cost = priced ? parseDecimalInput(line.cost, 2) : null;
    if (cost && !cost.ok) e.cost = cost.error;
    if (line.date && line.date > today) e.date = "La fecha de compra no puede ser futura.";
    else if (line.date && !priced) e.date = DATE_NEEDS_COST;
    errors.push(e);
    count += Object.keys(e).length;
    if (!line.asset || !units.ok || Object.keys(e).length > 0) continue;
    if (cost?.ok) {
      const p: PositionInitLine = {
        asset_id: line.asset.id,
        units: units.value,
        avg_cost_eur: cost.value,
      };
      if (line.date) p.acquired_at = dateInputToIso(line.date);
      plan.positions.push(p);
      plan.positionKeys.push(line.key);
    } else {
      plan.buys.push({ type: "buy", asset_id: line.asset.id, units: units.value });
      plan.buyKeys.push(line.key);
    }
  }
  return count > 0 ? { ok: false, errors, count } : { ok: true, ...plan };
}

/** Hoy en la zona de Madrid como "AAAA-MM-DD" (el `max` de los <input type="date">). */
export function todayInMadrid(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Madrid" }).format(now);
}
