/**
 * Tema claro/oscuro.
 *
 * El tema vive en `<html data-theme="light|dark">`. Lo fija primero un script en línea de
 * index.html (antes de pintar, sin parpadeo) con la misma lógica que `initialTheme`:
 * preferencia guardada y, si no hay, la del sistema. Aquí solo se lee y se cambia.
 */
export type Theme = "light" | "dark";

export const THEME_STORAGE_KEY = "kairos-theme";

const listeners = new Set<() => void>();

function isTheme(v: unknown): v is Theme {
  return v === "light" || v === "dark";
}

function readStored(): Theme | null {
  try {
    const v = localStorage.getItem(THEME_STORAGE_KEY);
    return isTheme(v) ? v : null;
  } catch {
    return null; // almacenamiento bloqueado (modo privado, políticas)
  }
}

function systemTheme(): Theme {
  return typeof matchMedia === "function" && matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function initialTheme(): Theme {
  return readStored() ?? systemTheme();
}

export function getTheme(): Theme {
  const v = document.documentElement.dataset.theme;
  return isTheme(v) ? v : initialTheme();
}

export function setTheme(theme: Theme): void {
  const root = document.documentElement;
  // Sin transiciones durante el cambio: todo cambia de color a la vez, sin fundidos a destiempo
  // (salvo el propio interruptor, marcado con data-keep-transition). Ver index.css.
  root.classList.add("theme-switching");
  root.dataset.theme = theme;
  requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove("theme-switching")));
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // sin persistencia: el cambio vale para esta visita
  }
  listeners.forEach((l) => l());
}

export function subscribeTheme(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
