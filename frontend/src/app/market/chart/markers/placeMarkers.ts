import type { EventImpactOut } from "../../../../api/generated/schema";
import type { ChartRow } from "../chartFormat";

/** Distancia máxima entre la fecha real del evento y el cierre en el que se dibuja (con `max` los
 *  puntos son semanales). */
const MAX_GAP_DAYS = 7;
const DAY_MS = 86_400_000;

export interface EventMarker {
  event: EventImpactOut;
  /** Fecha real del evento en el mercado (`market_date`). */
  marketDate: string;
  /** Cierre de la serie donde se dibuja (el más cercano, en el eje X de la gráfica). */
  date: string;
  /** Valor de la serie en ese cierre (solo para colocarlo en el eje Y). */
  value: number;
}

const dayOf = (iso: string) => Math.floor(Date.parse(iso) / DAY_MS);

/**
 * Coloca cada evento en el cierre más cercano a su fecha real (`market_date`), si hay uno a menos
 * de una semana. Los eventos sin `market_date` (guardados antes de existir el campo) o fuera del
 * periodo no se dibujan. Ordenados por fecha. Puro: sin red ni React.
 */
export function placeMarkers(rows: ChartRow[], events: EventImpactOut[]): EventMarker[] {
  if (rows.length === 0) return [];
  const days = rows.map((r) => dayOf(r.date));
  const markers: EventMarker[] = [];
  for (const event of events) {
    if (!event.market_date) continue;
    const target = dayOf(event.market_date);
    let best = -1;
    let gap = Infinity;
    days.forEach((d, i) => {
      const g = Math.abs(d - target);
      if (g < gap) {
        gap = g;
        best = i;
      }
    });
    const row = rows[best];
    if (!row || gap > MAX_GAP_DAYS) continue;
    markers.push({ event, marketDate: event.market_date, date: row.date, value: row.value });
  }
  return markers.sort((a, b) => a.marketDate.localeCompare(b.marketDate));
}

/**
 * Nivel de apilado de cada marcador (0 = sobre el punto, 1 = un piso más arriba…), para que dos
 * noticias cercanas no se pisen. `pxPerPoint` es el ancho de la gráfica entre el número de puntos.
 */
export function stackLevels(markers: EventMarker[], rows: ChartRow[], pxPerPoint: number, minGapPx = 34): Map<string, number> {
  const index = new Map(rows.map((r, i) => [r.date, i]));
  const levels = new Map<string, number>();
  let prev: { at: number; level: number } | null = null;
  for (const m of markers) {
    const at = index.get(m.date);
    if (at === undefined) continue;
    const level: number = prev && (at - prev.at) * pxPerPoint < minGapPx ? prev.level + 1 : 0;
    levels.set(m.event.event_id, level);
    prev = { at, level };
  }
  return levels;
}

/** Marcadores por fecha de cierre, para la tabla alternativa. */
export function markersByDate(markers: EventMarker[]): Map<string, EventMarker[]> {
  const map = new Map<string, EventMarker[]>();
  for (const m of markers) map.set(m.date, [...(map.get(m.date) ?? []), m]);
  return map;
}
