import { useEffect, useRef, useState, type RefObject } from "react";

/**
 * Ancho en píxeles de un elemento, que se actualiza al redimensionarlo. Sin `ResizeObserver`
 * (por ejemplo en los tests) se queda en el valor de reserva.
 */
export function useElementWidth<T extends HTMLElement>(fallback: number): [RefObject<T | null>, number] {
  const ref = useRef<T | null>(null);
  const [width, setWidth] = useState(fallback);

  useEffect(() => {
    const element = ref.current;
    if (!element || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => {
      const next = Math.round(entry?.contentRect.width ?? 0);
      if (next > 0) setWidth(next);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return [ref, width];
}
