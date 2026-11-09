import { useSyncExternalStore } from "react";
import { MoonIcon, SunIcon } from "../components/icons";
import { getTheme, setTheme, subscribeTheme } from "./theme";

interface ThemeToggleProps {
  /** Muestra el texto "Modo oscuro" y el interruptor visual (barra lateral). Si no, solo icono. */
  showLabel?: boolean;
}

/**
 * Interruptor de modo oscuro: <button role="switch" aria-checked>. El lector anuncia
 * "Modo oscuro, interruptor, activado/desactivado"; funciona con Intro y Espacio.
 * El nombre accesible es fijo: solo cambia aria-checked.
 */
export function ThemeToggle({ showLabel = false }: ThemeToggleProps) {
  const theme = useSyncExternalStore(subscribeTheme, getTheme, () => "light" as const);
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label={showLabel ? undefined : "Modo oscuro"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={[
        "inline-flex min-h-touch min-w-touch items-center gap-2.5 rounded-control text-base font-medium text-ink",
        showLabel
          ? "w-full justify-start whitespace-nowrap px-3 text-left hover:bg-surface"
          : "justify-center border border-line bg-surface px-2.5 hover:border-line-strong",
      ].join(" ")}
    >
      {isDark ? <MoonIcon className="size-5 shrink-0" /> : <SunIcon className="size-5 shrink-0" />}
      {showLabel && (
        <>
          <span>Modo oscuro</span>
          <span
            aria-hidden="true"
            data-keep-transition
            className={`ml-auto inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors duration-150 ${isDark ? "bg-accent" : "bg-line-strong"}`}
          >
            <span
              data-keep-transition
              className={`inline-block size-5 rounded-full bg-surface transition-transform duration-150 ${isDark ? "translate-x-[1.375rem]" : "translate-x-0.5"}`}
            />
          </span>
        </>
      )}
    </button>
  );
}
