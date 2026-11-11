import { useSyncExternalStore } from "react";
import type { AlertNewsMarker } from "./useAlertNewsMarkers";

export interface ActiveNewsMarker {
  marker: AlertNewsMarker;
  x: number;
  y: number;
}

export function createNewsMarkerStore() {
  let current: ActiveNewsMarker | null = null;
  const listeners = new Set<() => void>();
  return {
    get: () => current,
    set: (active: ActiveNewsMarker | null) => {
      if (active?.marker.news.id === current?.marker.news.id && active?.x === current?.x) return;
      current = active;
      listeners.forEach((listener) => listener());
    },
    subscribe: (listener: () => void) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

export type NewsMarkerStore = ReturnType<typeof createNewsMarkerStore>;

export function useActiveNewsMarker(store: NewsMarkerStore) {
  return useSyncExternalStore(store.subscribe, store.get, store.get);
}
