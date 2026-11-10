import { useMemo, useSyncExternalStore } from "react";

/**
 * Avisos leídos, por cartera, en el navegador (decisión de T2-20: sin ruta en el backend).
 * No hay login, así que «leído» es de quien mira en este navegador. Si el almacenamiento está
 * bloqueado (modo privado, políticas), se guarda en memoria y se pierde al recargar.
 */
const PREFIX = "kairos-alerts-read:";
/** Tope de ids guardados por cartera: tras cada `/demo/reset` los avisos cambian de id. */
const MAX_IDS = 200;

const memory = new Map<string, string>(); // solo si localStorage falla
const listeners = new Set<() => void>();

function load(portfolioId: string): string {
  const key = PREFIX + portfolioId;
  let stored: string | null = null;
  try {
    stored = localStorage.getItem(key);
  } catch {
    // almacenamiento bloqueado: queda la copia en memoria
  }
  return memory.get(key) ?? stored ?? "[]";
}

function parse(raw: string): string[] {
  try {
    const value: unknown = JSON.parse(raw);
    return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
  } catch {
    return [];
  }
}

function notify(): void {
  for (const listener of listeners) listener();
}

/** Marca como leídos esos avisos de la cartera (los demás leídos se conservan). */
export function markRead(portfolioId: string, ids: readonly string[]): void {
  if (ids.length === 0) return;
  const key = PREFIX + portfolioId;
  const raw = JSON.stringify([...new Set([...parse(load(portfolioId)), ...ids])].slice(-MAX_IDS));
  try {
    localStorage.setItem(key, raw);
  } catch {
    memory.set(key, raw);
  }
  notify();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  // Otra pestaña con la app abierta también marca avisos.
  const onStorage = (event: StorageEvent) => {
    if (event.key === null || event.key.startsWith(PREFIX)) listener();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

/** Ids de los avisos leídos de la cartera; se actualiza al marcar desde cualquier campana. */
export function useReadIds(portfolioId: string): ReadonlySet<string> {
  const raw = useSyncExternalStore(
    subscribe,
    () => load(portfolioId),
    () => "[]",
  );
  return useMemo(() => new Set(parse(raw)), [raw]);
}
