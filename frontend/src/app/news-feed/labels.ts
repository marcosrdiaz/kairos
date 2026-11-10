import type {
  EffectTiming,
  NewsCategory,
  NewsDirection,
  NewsEstimateOut,
  NewsEstimateStatus,
} from "../../api/generated/schema";
import { formatDate, formatEurRange, formatPercent } from "../../lib/format";

/** Orden de los filtros de la pantalla Noticias. */
export const CATEGORIES: NewsCategory[] = [
  "company",
  "earnings",
  "central_bank",
  "politics",
  "commodities",
  "fx",
  "other",
];

export const CATEGORY_LABEL: Record<NewsCategory, string> = {
  company: "Empresas",
  earnings: "Resultados",
  central_bank: "Bancos centrales",
  politics: "Política",
  commodities: "Materias primas",
  fx: "Divisas",
  other: "Otras",
};

export const STATUS_LABEL: Record<NewsEstimateStatus, string> = {
  estimated: "Estimado",
  measured: "Medido",
  pending: "Calculando",
  not_relevant: "No afecta a tu cartera",
};

export const DIRECTION_LABEL: Record<NewsDirection, string> = {
  up: "al alza",
  down: "a la baja",
  uncertain: "dirección incierta",
};

export const TIMING_LABEL: Record<EffectTiming, string> = {
  same_session: "Se nota en la sesión",
  next_nav: "Se nota con el siguiente valor liquidativo",
  no_daily_price: "Sin precio diario",
};

/** "en la próxima sesión" / "en las próximas 5 sesiones". */
export function horizonText(sessions: number): string {
  return sessions === 1 ? "en la próxima sesión" : `en las próximas ${sessions} sesiones`;
}

/** De dónde sale el rango, en palabras: nunca del modelo de lenguaje. */
export function methodText(estimate: NewsEstimateOut): string {
  switch (estimate.method) {
    case "analogs": {
      const n = estimate.analogs_count;
      return n ? `Según ${n} casos parecidos del histórico` : "Según casos parecidos del histórico";
    }
    case "volatility":
      return "Según la volatilidad histórica (pocos casos parecidos)";
    case "measured":
      return "Medido con los precios de cierre";
    default:
      return "";
  }
}

/** "entre -270 € y -110 €" y "entre -0,6 % y -0,3 %", o null si la estimación no tiene cifras. */
export function rangeTexts(estimate: NewsEstimateOut): { eur: string; pct: string } | null {
  const { low_eur, high_eur, low_pct, high_pct } = estimate;
  if (!low_eur || !high_eur || !low_pct || !high_pct) return null;
  return {
    eur: formatEurRange(low_eur, high_eur),
    pct: `entre ${formatPercent(low_pct)} y ${formatPercent(high_pct)}`,
  };
}

/** "Se nota en la sesión · desde el 20 de noviembre de 2026". */
export function timingText(timing: EffectTiming, effectiveFrom: string | null): string {
  const label = TIMING_LABEL[timing];
  return effectiveFrom ? `${label} · desde el ${formatDate(effectiveFrom)}` : label;
}
