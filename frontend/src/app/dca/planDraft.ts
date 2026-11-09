import type {
  AssetOut,
  DcaAllocation,
  DcaPlanOut,
  Frequency,
  PortfolioOut,
} from "../../api/generated/schema";
import { parseDecimalInput } from "../onboarding/decimalInput";
import { ASSET_TYPE_LABEL, assetDetails } from "../onboarding/labels";

/** Activo del reparto: lo justo para mostrarlo y enviarlo. */
export interface AssetRef {
  id: string;
  name: string;
  details: string | null;
}

export interface AllocationLine {
  key: number;
  asset: AssetRef | null;
  /** Porcentaje tal como lo escribe el usuario ("70" o "33,5"). */
  percent: string;
}

export interface PlanDraft {
  amount: string;
  frequency: Frequency;
  /** Día del mes (1-28) o de la semana (1 = lunes … 7 = domingo), como string del <select>. */
  day: string;
  lines: AllocationLine[];
}

export interface PlanErrors {
  amount?: string;
  lines: { asset?: string; percent?: string }[];
  /** El reparto entero (no suma 100 %). */
  total?: string;
}

export interface PlanBody {
  amount_eur: string;
  frequency: Frequency;
  day: number;
  allocations: DcaAllocation[];
}

export const DUPLICATE_ASSET = "Este activo ya está en el reparto.";

let nextKey = 0;
export const emptyLine = (asset: AssetRef | null = null, percent = ""): AllocationLine => ({
  key: nextKey++,
  asset,
  percent,
});

export const emptyPlan = (): PlanDraft => ({
  amount: "",
  frequency: "monthly",
  day: "1",
  lines: [emptyLine()],
});

export const refFromAsset = (a: AssetOut): AssetRef => ({ id: a.id, name: a.name, details: assetDetails(a) });

/** Activo del reparto a partir de la cartera; si no está en ella, solo su identificador. */
export function refFromId(portfolio: PortfolioOut | undefined, assetId: string): AssetRef {
  const p = portfolio?.positions.find((x) => x.asset_id === assetId);
  if (!p) return { id: assetId, name: assetId, details: null };
  return {
    id: assetId,
    name: p.name,
    details: [p.isin, p.ticker, ASSET_TYPE_LABEL[p.asset_type]].filter(Boolean).join(" · "),
  };
}

/*
 * Pesos exactos sin coma flotante: el porcentaje (hasta 6 decimales, que con los 2 del "%"
 * son los 8 de `Numeric(10,8)` en BD) se pasa a un entero de cienmillonésimas
 * (100 % = 10^8) moviendo la coma en el texto. Así "Σ = 100 %" se comprueba sin redondeos,
 * igual que el backend con `Decimal` (Σ weight = 1 exacto). 10^8 cabe de sobra en un entero
 * exacto de JavaScript.
 */
const PERCENT_DECIMALS = 6;
const FULL = 100_000_000;

function percentToUnits(value: string): number {
  const [int = "0", frac = ""] = value.split(".");
  return Number(int) * 10 ** PERCENT_DECIMALS + Number(frac.padEnd(PERCENT_DECIMALS, "0"));
}

/** 70000000 -> "0.7" (fracción para `DcaAllocation.weight`). */
function unitsToWeight(m: number): string {
  const s = String(m).padStart(9, "0");
  return `${s.slice(0, -8)}.${s.slice(-8)}`.replace(/\.?0+$/, "");
}

/** 90000000 -> "90" ; 33330000 -> "33,33" (para mensajes). */
function unitsToPercent(m: number): string {
  const s = String(m).padStart(7, "0");
  return `${s.slice(0, -6)},${s.slice(-6)}`.replace(/,?0+$/, "");
}

/** Fracción del backend ("0.7") al porcentaje que se edita ("70"). */
export function weightToPercent(weight: string): string {
  const [int = "0", frac = ""] = weight.split(".");
  const shifted = `${int}${frac.padEnd(2, "0").slice(0, 2)}`.replace(/^0+(?=\d)/, "");
  const rest = frac.slice(2).replace(/0+$/, "");
  return rest ? `${shifted},${rest}` : shifted;
}

export function draftFromPlan(plan: DcaPlanOut, portfolio: PortfolioOut | undefined): PlanDraft {
  return {
    amount: plan.amount_eur.replace(".", ","),
    frequency: plan.frequency,
    day: String(plan.day),
    lines: plan.allocations.map((a) => emptyLine(refFromId(portfolio, a.asset_id), weightToPercent(a.weight))),
  };
}

export type BuiltPlan = { ok: true; body: PlanBody } | { ok: false; errors: PlanErrors; count: number };

/** Valida el borrador del plan (UC-04: importe, frecuencia, día y reparto con Σ = 100 %). */
export function buildPlan(draft: PlanDraft): BuiltPlan {
  const errors: PlanErrors = { lines: draft.lines.map(() => ({})) };
  let count = 0;
  const amount = parseDecimalInput(draft.amount, 2);
  if (!amount.ok) {
    errors.amount = amount.error;
    count++;
  }
  const seen = new Set<string>();
  const allocations: DcaAllocation[] = [];
  let total = 0;
  let linesOk = true;
  draft.lines.forEach((line, i) => {
    const e = errors.lines[i]!;
    if (!line.asset) e.asset = "Elige el activo.";
    else if (seen.has(line.asset.id)) e.asset = DUPLICATE_ASSET;
    else seen.add(line.asset.id);
    const pct = parseDecimalInput(line.percent, PERCENT_DECIMALS);
    if (!pct.ok) e.percent = pct.error;
    else if (percentToUnits(pct.value) > FULL) e.percent = "Como mucho 100 %.";
    if (e.asset || e.percent) {
      count += Number(Boolean(e.asset)) + Number(Boolean(e.percent));
      linesOk = false;
      return;
    }
    if (pct.ok && line.asset) {
      const m = percentToUnits(pct.value);
      total += m;
      allocations.push({ asset_id: line.asset.id, weight: unitsToWeight(m) });
    }
  });
  if (linesOk && total !== FULL) {
    errors.total = `El reparto suma ${unitsToPercent(total)} % y tiene que sumar 100 %.`;
    count++;
  }
  if (count > 0 || !amount.ok) return { ok: false, errors, count };
  return {
    ok: true,
    body: { amount_eur: amount.value, frequency: draft.frequency, day: Number(draft.day), allocations },
  };
}

/** Errores que quedan por revisar (para el resumen del formulario). */
export function countPlanErrors(e: PlanErrors): number {
  const lines = e.lines.reduce((n, l) => n + Number(Boolean(l.asset)) + Number(Boolean(l.percent)), 0);
  return Number(Boolean(e.amount)) + Number(Boolean(e.total)) + lines;
}

/**
 * Tras editar el reparto, conserva solo los errores de las filas que no han cambiado (misma
 * referencia) y quita el del total, que depende de todas: el usuario está corrigiendo.
 * "Activo repetido" depende de las demás filas: se mantiene solo si una fila anterior sigue
 * teniendo el mismo activo (la misma regla que `buildPlan`).
 */
export function carryLineErrors(
  errors: PlanErrors,
  before: AllocationLine[],
  after: AllocationLine[],
): PlanErrors {
  const lines = after.map((line, j) => {
    const i = before.indexOf(line);
    const kept = i >= 0 ? { ...(errors.lines[i] ?? {}) } : {};
    const id = line.asset?.id;
    const stillRepeated = id !== undefined && after.slice(0, j).some((l) => l.asset?.id === id);
    if (kept.asset === DUPLICATE_ASSET && !stillRepeated) delete kept.asset;
    return kept;
  });
  const next: PlanErrors = { ...errors, lines };
  delete next.total;
  return next;
}
