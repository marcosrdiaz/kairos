import { useEffect, useId, useMemo, useRef, useState, type ComponentProps } from "react";
import { HistoryChart } from "../HistoryChart";
import { MarkerCard } from "./MarkerCard";
import { AlertNewsCard } from "./AlertNewsCard";
import { createNewsMarkerStore, useActiveNewsMarker } from "./newsMarkerStore";
import type { AlertNewsMarker } from "./useAlertNewsMarkers";
import { createMarkerStore, useActiveMarker } from "./markerStore";
import { stackLevels, type EventMarker } from "./placeMarkers";

type MarkedChartProps = Omit<
  ComponentProps<typeof HistoryChart>,
  "markers" | "markerLevels" | "markerStore" | "markerCardId" | "newsMarkers" | "newsMarkerStore" | "newsCardId"
> & {
  /** Marcadores de toda la serie; aquí se dibujan los del tramo visible. */
  markers: EventMarker[];
  newsMarkers?: AlertNewsMarker[];
  /** Clases del contenedor (alto, cuando la gráfica rellena su hueco). */
  className?: string;
};

/** Ancho y alto del contenedor, para que la tarjeta no se salga de él. */
function useSize() {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const measure = () => setSize({ width: el.clientWidth, height: el.clientHeight });
    measure();
    if (typeof ResizeObserver !== "function") return;
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return [ref, size] as const;
}

/**
 * Gráfica de evolución con las noticias encima (T2-22): marcadores en la fecha real de cada evento
 * y la tarjeta del activo. La tarjeta lee su propio almacén, así que abrirla no repinta la gráfica.
 */
export function MarkedChart({ markers, newsMarkers = [], rows, className = "", ...chart }: MarkedChartProps) {
  const [store] = useState(createMarkerStore);
  const [newsStore] = useState(createNewsMarkerStore);
  const cardId = useId();
  const newsCardId = useId();
  const [ref, { width, height }] = useSize();
  // Solo cambia un atributo del contenedor: la gráfica (memo) no se vuelve a renderizar.
  const active = useActiveMarker(store);
  const activeNews = useActiveNewsMarker(newsStore);
  const visible = useMemo(() => {
    const dates = new Set(rows.map((r) => r.date));
    return markers.filter((m) => dates.has(m.date));
  }, [markers, rows]);
  // Apilado según el ancho real: lo que en «Todo» queda pegado, en 1A ya cabe lado a lado.
  const levels = useMemo(
    () => stackLevels(visible, rows, width / Math.max(rows.length - 1, 1)),
    [visible, rows, width],
  );
  const visibleNews = useMemo(() => {
    const dates = new Set(rows.map((r) => r.date));
    return newsMarkers.filter((m) => dates.has(m.date));
  }, [newsMarkers, rows]);
  return (
    <div
      ref={ref}
      className={`relative ${className}`}
      data-marker-active={active || activeNews ? "" : undefined}
      onMouseLeave={() => newsStore.set(null)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) newsStore.set(null);
      }}
    >
      <HistoryChart
        {...chart}
        rows={rows}
        markers={visible}
        markerLevels={levels}
        markerStore={store}
        markerCardId={cardId}
        newsMarkers={visibleNews}
        newsMarkerStore={newsStore}
        newsCardId={newsCardId}
      />
      <MarkerCard store={store} id={cardId} width={width} />
      <AlertNewsCard store={newsStore} id={newsCardId} width={width} height={height} />
    </div>
  );
}
