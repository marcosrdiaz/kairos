import { useSyncExternalStore } from "react";
import type { EventMarker } from "./placeMarkers";

/** Marcador activo (ratón o foco) y su posición en píxeles dentro de la gráfica. */
export interface ActiveMarker {
  marker: EventMarker;
  x: number;
  y: number;
}

/**
 * Marcador activo fuera del estado de React, como el punto activo (`activePoint.ts`): al pasar
 * por un marcador solo se repinta la tarjeta, no la gráfica.
 */
export interface MarkerStore {
  get: () => ActiveMarker | null;
  set: (active: ActiveMarker | null) => void;
  subscribe: (listener: () => void) => () => void;
}

export function createMarkerStore(): MarkerStore {
  let current: ActiveMarker | null = null;
  const listeners = new Set<() => void>();
  return {
    get: () => current,
    set: (active) => {
      if (active?.marker.event.event_id === current?.marker.event.event_id && active?.x === current?.x) return;
      current = active;
      listeners.forEach((l) => l());
    },
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

export function useActiveMarker(store: MarkerStore): ActiveMarker | null {
  return useSyncExternalStore(store.subscribe, store.get, store.get);
}
