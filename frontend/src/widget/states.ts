import type { StatusReasonKind, StatusState } from "../api/generated/schema";
import { formatPercent } from "../lib/format";

/** Colores por estado (tokens de index.css). Siempre van junto a la palabra: nunca solo color. */
const STATE_CLASSES: Record<StatusState, string> = {
  tranquilo: "bg-tranquilo-bg text-tranquilo",
  atento: "bg-atento-bg text-atento",
  revisa_plan: "bg-revisa-plan-bg text-revisa-plan",
};

const STATE_BAND: Record<StatusState, string> = {
  tranquilo: "bg-tranquilo-solid",
  atento: "bg-atento-solid",
  revisa_plan: "bg-revisa-plan-solid",
};

/** Palabra por defecto si el backend no trae `state_label`. */
export const STATE_WORD: Record<StatusState, string> = {
  tranquilo: "Tranquilo",
  atento: "Atento",
  revisa_plan: "Revisa tu plan",
};

export function stateClasses(state: StatusState): string {
  return STATE_CLASSES[state];
}

/** Motivo del estado en palabras (sin cifras: el impacto en € va con rango en el panel). */
export const REASON_TEXT: Record<StatusReasonKind, string> = {
  event: "Un evento reciente",
  drift: "Desvío de tu plan",
  none: "Nada destacable",
};

/** "-0.015" -> "-1,5 %"; "0.012" -> "+1,2 %"; "0" -> "0,0 %". El signo explícito no depende del color. */
export function signedPercent(fraction: string): string {
  const v = fraction.trim();
  const text = formatPercent(v);
  const isZero = /^[+-]?0*(\.0*)?$/.test(v);
  return v.startsWith("-") || isZero ? text : `+${text}`;
}

export function trendOf(fraction: string): "up" | "down" | "flat" {
  const v = fraction.trim();
  if (/^[+-]?0*(\.0*)?$/.test(v)) return "flat";
  return v.startsWith("-") ? "down" : "up";
}

/** Franja de color sólido del estado (decorativa: la palabra va en la insignia). */
export function stateBandClass(state: StatusState): string {
  return STATE_BAND[state];
}
