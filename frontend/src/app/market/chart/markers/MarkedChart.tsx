import { useEffect, useId, useMemo, useRef, useState, type ComponentProps } from "react";
import { HistoryChart } from "../HistoryChart";
import { MarkerCard } from "./MarkerCard";
import { createMarkerStore, useActiveMarker } from "./markerStore";
import { stackLevels, type EventMarker } from "./placeMarkers";

type MarkedChartProps = Omit<
  ComponentProps<typeof HistoryChart>,
  "markers" | "markerLevels" | "markerStore" | "markerCardId"
> & {
  /** Marcadores de toda la serie; aquí se dibujan los del tramo visible. */
  markers: EventMarker[];
};

/** Ancho del contenedor, para que la tarjeta no se salga por los lados. */
function useWidth() {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    setWidth(el.clientWidth);
    if (typeof ResizeObserver !== "function") return;
    const observer = new ResizeObserver(() => setWidth(el.clientWidth));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

/**
 * Gráfica de evolución con las noticias encima (T2-22): marcadores en la fecha real de cada evento
 * y la tarjeta del activo. La tarjeta lee su propio almacén, así que abrirla no repinta la gráfica.
 */
export function MarkedChart({ markers, rows, ...chart }: MarkedChartProps) {
  const [store] = useState(createMarkerStore);
  const cardId = useId();
  const [ref, width] = useWidth();
  // Solo cambia un atributo del contenedor: la gráfica (memo) no se vuelve a renderizar.
  const active = useActiveMarker(store);
  const visible = useMemo(() => {
    const dates = new Set(rows.map((r) => r.date));
    return markers.filter((m) => dates.has(m.date));
  }, [markers, rows]);
  // Apilado según el ancho real: lo que en «Todo» queda pegado, en 1A ya cabe lado a lado.
  const levels = useMemo(
    () => stackLevels(visible, rows, width / Math.max(rows.length - 1, 1)),
    [visible, rows, width],
  );
  return (
    <div ref={ref} className="relative" data-marker-active={active ? "" : undefined}>
      <HistoryChart
        {...chart}
        rows={rows}
        markers={visible}
        markerLevels={levels}
        markerStore={store}
        markerCardId={cardId}
      />
      <MarkerCard store={store} id={cardId} width={width} />
    </div>
  );
}
