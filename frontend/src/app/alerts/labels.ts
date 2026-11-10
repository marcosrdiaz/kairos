import type { AlertOut } from "../../api/generated/schema";

/**
 * Tipo de aviso en palabras. Es un mapa abierto: `market_move` (T2-21) llega antes que su tipo
 * generado, y un tipo desconocido se muestra como «Aviso» en vez de romper la lista.
 */
const KIND_LABEL: Record<AlertOut["kind"] | "market_move", string> = {
  event_impact: "Noticia que afecta a tu cartera",
  news_estimate: "Impacto estimado de una noticia",
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

/**
 * Bandeja vacía. `undefined`: solo hay una cartera. `null`: varias, sin filtro. Un nombre: la
 * cartera filtrada.
 */
export function emptyInboxText(portfolioName: string | null | undefined): string {
  if (portfolioName === undefined) {
    return "Todavía no hay avisos de esta cartera. Te avisaremos cuando una noticia la mueva lo bastante.";
  }
  if (portfolioName === null) {
    return "Todavía no hay avisos de ninguna de tus carteras. Te avisaremos cuando una noticia mueva alguna lo bastante.";
  }
  return `Todavía no hay avisos de la cartera «${portfolioName}». Te avisaremos cuando una noticia la mueva lo bastante.`;
}

/** Pie de la bandeja (RF-20): los mensajes los redacta una IA y no son asesoramiento. */
export const INBOX_NOTICE =
  "Los avisos los redacta una inteligencia artificial a partir de cálculos sobre tu cartera. Son contexto, no asesoramiento financiero.";
