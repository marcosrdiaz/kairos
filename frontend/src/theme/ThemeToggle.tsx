import { useSyncExternalStore } from "react";
import { MoonIcon, SunIcon } from "../components/icons";
import { getTheme, setTheme, subscribeTheme } from "./theme";

interface ThemeToggleProps {
  /** Muestra el texto "Modo oscuro" junto al icono (barra lateral). Si no, solo icono con nombre accesible. */
  showLabel?: boolean;
}

/**
 * Interruptor de modo oscuro. Es un <button aria-pressed>: el lector anuncia
 * "Modo oscuro, botón de alternancia, activado/desactivado"; funciona con Intro y Espacio.
 * El nombre accesible no cambia con el estado (solo cambia aria-pressed), como pide WAI-ARIA.
 */
export function ThemeToggle({ showLabel = false }: ThemeToggleProps) {
  const theme = useSyncExternalStore(subscribeTheme, getTheme, () => "light" as const);
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      aria-pressed={isDark}
      aria-label={showLabel ? undefined : "Modo oscuro"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={`inline-flex min-h-touch min-w-touch items-center justify-center gap-3 rounded-control border border-line bg-surface px-3 text-base font-medium text-ink hover:border-line-strong ${showLabel ? "w-full" : ""}`}
    >
      {isDark ? <MoonIcon className="size-5" /> : <SunIcon className="size-5" />}
      {showLabel && <span>Modo oscuro</span>}
      {showLabel && (
        <span
          aria-hidden="true"
          className={`relative ml-auto inline-block h-6 w-10 rounded-full border border-line-strong transition-colors ${isDark ? "bg-accent" : "bg-surface-muted"}`}
        >
          <span
            className={`absolute top-0.5 size-4.5 rounded-full transition-transform ${isDark ? "translate-x-[1.125rem] bg-on-accent" : "translate-x-0.5 bg-line-strong"}`}
          />
        </span>
      )}
    </button>
  );
}
