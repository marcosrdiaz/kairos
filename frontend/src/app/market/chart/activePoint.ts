import { useSyncExternalStore } from "react";
import type { ChartRow } from "./chartFormat";

/**
 * Punto activo de la gráfica (ratón o teclado), fuera del estado de React del contenedor:
 * al mover el ratón solo se vuelven a pintar quienes lo leen (la cifra destacada y la región
 * `aria-live`), no la gráfica, la escala de tiempo ni la tabla. Uno por gráfica.
 */
export interface ActivePointStore {
  get: () => ChartRow | null;
  set: (row: ChartRow | null) => void;
  subscribe: (listener: () => void) => () => void;
}

export function createActivePointStore(): ActivePointStore {
  let current: ChartRow | null = null;
  const listeners = new Set<() => void>();
  return {
    get: () => current,
    set: (row) => {
      if (row?.date === current?.date) return;
      current = row;
      listeners.forEach((l) => l());
    },
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

export function useActivePoint(store: ActivePointStore): ChartRow | null {
  return useSyncExternalStore(store.subscribe, store.get, store.get);
}
