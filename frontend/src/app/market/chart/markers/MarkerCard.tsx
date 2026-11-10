import type { Factor } from "../../../../api/generated/schema";
import { ArrowDownIcon, ArrowUpIcon } from "../../../../components/icons";
import { FIELD_LABEL } from "../../../../components/trace/labels";
import { CONFIDENCE_LABEL, EVENT_TYPE_LABEL } from "../../../news/labels";
import { pointDate, signedPct, trendOf } from "../chartFormat";
import { useActiveMarker, type MarkerStore } from "./markerStore";
import { markerImpact, markerSummary } from "./markerText";

const CARD_WIDTH = 320;
/** Desde qué altura (px dentro de la gráfica) la tarjeta se abre hacia arriba. */
const ABOVE_FROM_Y = 220;
const TONE = { up: "text-trend-up", down: "text-trend-loss", flat: "text-ink-muted" } as const;

/** Movimiento de un factor ese día: nombre, flecha, signo y color (nunca solo color). */
function FactorMove({ factor, move }: { factor: Factor; move: string }) {
  const trend = trendOf(move);
  const Icon = trend === "up" ? ArrowUpIcon : trend === "down" ? ArrowDownIcon : null;
  return (
    <li className="flex items-center justify-between gap-3">
      <span>{FIELD_LABEL[factor] ?? factor}</span>
      <span className={`inline-flex items-center gap-1 font-medium tabular-nums ${TONE[trend]}`}>
        {Icon && <Icon className="size-3.5" />}
        {signedPct(move)}
      </span>
    </li>
  );
}

interface MarkerCardProps {
  store: MarkerStore;
  id: string;
  /** Ancho de la gráfica, para que la tarjeta no se salga por los lados. */
  width: number;
}

/**
 * Tarjeta de la noticia del marcador activo: tipo y fecha real, título, descripción breve,
 * movimiento observado del mercado (factores del `ShockSet`) e impacto en la cartera con rango,
 * confianza y de dónde sale. Solo informativa: no captura el ratón. Las cifras son del backend.
 * Siempre está en el DOM (con `hidden`) para que `aria-describedby` del marcador la encuentre.
 */
export function MarkerCard({ store, id, width }: MarkerCardProps) {
  const active = useActiveMarker(store);
  const e = active?.marker.event;
  const left = active ? Math.min(Math.max(active.x - CARD_WIDTH / 2, 0), Math.max(width - CARD_WIDTH, 0)) : 0;
  // Debajo del marcador (hay sitio de sobra: debajo vienen la escala y la tabla); si el marcador
  // está muy abajo en la gráfica, encima.
  const above = (active?.y ?? 0) > ABOVE_FROM_Y;
  const top = active ? (above ? active.y - 24 : active.y + 24) : 0;
  const moves = Object.entries(e?.factor_moves ?? {}) as [Factor, string][];
  const impact = active ? markerImpact(active.marker) : null;
  return (
    <div
      id={id}
      role="tooltip"
      hidden={!active}
      className="kchart-tip pointer-events-none absolute z-20 flex flex-col gap-2 px-4 py-3 text-sm"
      style={{ left, top, width: CARD_WIDTH, translate: above ? "0 -100%" : "0 0" }}
    >
      {active && e && (
        <>
          <p className="m-0 text-xs font-semibold uppercase tracking-wider text-accent">
            {EVENT_TYPE_LABEL[e.event_type]} · {pointDate(active.marker.marketDate)}
          </p>
          <p className="m-0 text-base font-semibold leading-snug text-ink">{e.title}</p>
          <p className="m-0 line-clamp-3 text-ink-muted">{markerSummary(active.marker)}</p>
          {moves.length > 0 && (
            <div>
              <p className="m-0 mb-1 font-semibold text-ink">El mercado ese día</p>
              <ul className="m-0 flex list-none flex-col gap-0.5 p-0 text-ink-muted">
                {moves.map(([factor, move]) => (
                  <FactorMove key={factor} factor={factor} move={move} />
                ))}
              </ul>
            </div>
          )}
          <div className="border-t border-line pt-2">
            <p className="m-0 font-semibold text-ink">Impacto estimado {impact?.scope}</p>
            <p className="m-0 tabular-nums text-ink" data-calc-id={e.calc_id}>
              {impact?.range}
              <span className="text-ink-muted"> · {CONFIDENCE_LABEL[e.confidence]}</span>
            </p>
            <p className="m-0 mt-1 text-xs text-ink-muted">
              De dónde sale: el movimiento de ese día aplicado a tus fondos y acciones según cómo
              reaccionan a cada factor. {e.sources[0] ? `Fuente: ${e.sources[0].label}.` : ""}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
