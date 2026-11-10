/**
 * Textos de los avisos legales (regla 6 de producto, RF-20):
 * - Aviso de IA (AI Act, art. 50): quien usa la app sabe que las explicaciones las redacta una IA.
 * - "No es asesoramiento" (MiFID II): Kairos da contexto, no recomienda operaciones.
 * Sin cifras y sin verbos de orden: son textos fijos, no pasan por el guardián.
 */

/** Pie de todas las pantallas de la app (AppShell). */
export const APP_NOTICE =
  "Kairos usa inteligencia artificial para redactar las explicaciones. No es asesoramiento financiero.";

export const PANEL_NOTICE_TITLE = "Información, no asesoramiento";

/** Aviso del panel de contexto, una idea por frase. */
export const PANEL_NOTICE_LINES = [
  "Las explicaciones las redacta una inteligencia artificial. Las cifras no: salen de cálculos sobre la cartera, y cada una dice de dónde sale.",
  "Los impactos son estimaciones con un rango y una confianza, no previsiones exactas.",
  "Kairos da contexto frente al plan de cada inversor. No es asesoramiento financiero ni recomienda operaciones.",
] as const;
