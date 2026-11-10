import type { AlertOut } from "../../api/generated/schema";

/**
 * Tipo de aviso en palabras. Es un mapa abierto: `market_move` (T2-21) llega antes que su tipo
 * generado, y un tipo desconocido se muestra como «Aviso» en vez de romper la lista.
 */
const KIND_LABEL: Record<AlertOut["kind"] | "market_move", string> = {
  event_impact: "Noticia que afecta a tu cartera",
  market_move: "Movimiento de tu cartera",
  dca_pending: "Aportación periódica pendiente",
  drift: "Tu cartera se aleja del plan",
};

export function kindLabel(kind: string): string {
  return (KIND_LABEL as Record<string, string>)[kind] ?? "Aviso";
}

/** Nombre accesible de la campana: el número no depende solo del globo visual. */
export function bellLabel(unread: number): string {
  if (unread === 0) return "Avisos, ninguno sin leer";
  return unread === 1 ? "Avisos, 1 sin leer" : `Avisos, ${unread} sin leer`;
}

/** Texto del globo: más de 9 se resume para que quepa. */
export function badgeText(unread: number): string {
  return unread > 9 ? "9+" : String(unread);
}

/** Pie de la bandeja (RF-20): los mensajes los redacta una IA y no son asesoramiento. */
export const INBOX_NOTICE =
  "Los avisos los redacta una inteligencia artificial a partir de cálculos sobre tu cartera. Son contexto, no asesoramiento financiero.";
