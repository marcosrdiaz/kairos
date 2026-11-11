import { usePortfolios } from "../app/portfolio-picker/usePortfolios";
import { PANEL_SECTIONS } from "./sections";

interface PanelHeaderProps {
  portfolioId: string;
}

/**
 * Navegación interna de los bloques, dentro del contenido de AppShell.
 * Un aviso `aria-live` dice qué cartera se está viendo al cambiarla desde Cartera.
 */
export function PanelHeader({ portfolioId }: PanelHeaderProps) {
  const { data } = usePortfolios();
  const name = data?.find((p) => p.id === portfolioId)?.name;

  return (
    <div className="flex flex-col gap-2">
      {name && <p className="m-0 text-base text-ink-muted">Cartera: {name}</p>}
      <nav aria-label="Bloques del panel" className="flex flex-wrap items-center gap-1">
        {PANEL_SECTIONS.map((s) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            className="inline-flex min-h-touch items-center rounded-control px-3 text-base font-medium text-ink-muted no-underline hover:bg-surface-muted hover:text-ink"
          >
            {s.label}
          </a>
        ))}
      </nav>
      <p role="status" aria-live="polite" className="sr-only">
        {name ? `Mostrando la cartera de ${name}` : ""}
      </p>
    </div>
  );
}
