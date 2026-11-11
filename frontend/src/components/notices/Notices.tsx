import { APP_NOTICE, PANEL_NOTICE_LINES, PANEL_NOTICE_TITLE } from "./texts";

/** Icono de información, decorativo: el significado lo da el texto. */
function InfoIcon({ className }: { className: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5" />
      <path d="M12 8h.01" />
    </svg>
  );
}

/**
 * Aviso del panel de contexto (RF-20): IA, cifras calculadas, rangos y "no es asesoramiento".
 * Es una región con nombre para que el lector de pantalla la anuncie y se pueda saltar a ella.
 */
export function PanelNotice() {
  return (
    <section
      aria-labelledby="aviso-panel-titulo"
      className="flex gap-3 rounded-card border border-line bg-surface p-4 sm:gap-4 sm:p-5"
    >
      <InfoIcon className="mt-0.5 size-6 shrink-0 text-accent" />
      <div className="flex flex-col gap-2">
        <h2 id="aviso-panel-titulo" className="m-0 text-base font-semibold text-ink">
          {PANEL_NOTICE_TITLE}
        </h2>
        {/* En pantalla ancha, los tres avisos van en columnas: el bloque ocupa la mitad de alto. */}
        <ul className="m-0 flex list-none flex-col gap-1 p-0 text-sm text-ink-muted lg:grid lg:grid-cols-3 lg:gap-6">
          {PANEL_NOTICE_LINES.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}

/** Pie de todas las pantallas de la app (AppShell): aviso de IA y "no es asesoramiento". */
export function AppNotice() {
  return (
    <p className="m-0 mt-10 flex items-start gap-2 border-t border-line pt-4 text-sm text-ink-muted">
      <InfoIcon className="mt-0.5 size-5 shrink-0" />
      <span>{APP_NOTICE}</span>
    </p>
  );
}
