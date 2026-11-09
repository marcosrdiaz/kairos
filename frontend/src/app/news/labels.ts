import type { Confidence, EventImpactOut, Polarity } from "../../api/generated/schema";

/** El esquema generado no exporta el enum con nombre: se deriva del contrato. */
export type EventType = EventImpactOut["event_type"];

export const EVENT_TYPE_LABEL: Record<EventType, string> = {
  central_bank: "Banco central",
  commodity: "Materias primas",
  earnings: "Resultados",
  fx: "Divisas",
  macro: "Macroeconomía",
};

/** Polaridad en palabras + color, sin rojo: el riesgo usa el ámbar de "Atento". */
export const POLARITY: Record<Polarity, { label: string; className: string }> = {
  riesgo: { label: "Riesgo", className: "bg-atento-bg text-atento" },
  oportunidad: { label: "Oportunidad", className: "bg-tranquilo-bg text-tranquilo" },
  neutral: { label: "Neutral", className: "bg-nodata-bg text-nodata" },
};

export const CONFIDENCE_LABEL: Record<Confidence, string> = {
  alta: "Confianza alta",
  media: "Confianza media",
  baja: "Confianza baja",
};

/** Intervalo del avance automático del carrusel. */
export const AUTO_ADVANCE_MS = 10_000;
