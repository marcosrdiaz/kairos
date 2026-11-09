import type { StatusState } from "../api/generated/schema";

/** Colores por estado (tokens de index.css). Siempre van junto a la palabra: nunca solo color. */
const STATE_CLASSES: Record<StatusState, string> = {
  tranquilo: "bg-tranquilo-bg text-tranquilo",
  atento: "bg-atento-bg text-atento",
  revisa_plan: "bg-revisa-plan-bg text-revisa-plan",
};

const STATE_BAND: Record<StatusState, string> = {
  tranquilo: "bg-tranquilo",
  atento: "bg-atento",
  revisa_plan: "bg-revisa-plan",
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

/** Franja de color sólido del estado (decorativa: la palabra va en la insignia). */
export function stateBandClass(state: StatusState): string {
  return STATE_BAND[state];
}
