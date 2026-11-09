/**
 * Clases de botón compartidas (para <button> y para <Link> con aspecto de botón).
 * Altura mínima de 44 px, foco con el anillo global (:focus-visible) y estado deshabilitado
 * que no depende solo del color (cursor y aria-disabled los pone quien lo usa).
 */
const base =
  "inline-flex min-h-touch items-center justify-center gap-2 rounded-full px-5 text-base font-semibold no-underline transition-colors";

export const buttonPrimary = `${base} bg-accent text-on-accent hover:bg-accent-hover`;

export const buttonSecondary = `${base} border border-line-strong bg-surface text-ink hover:bg-surface-muted`;

export const buttonDisabled = `${base} cursor-not-allowed bg-nodata-bg text-nodata`;
