import { Link, useSearchParams } from "react-router";
import { PortfolioPicker } from "../app/portfolio-picker/PortfolioPicker";
import { usePortfolios } from "../app/portfolio-picker/usePortfolios";
import { PANEL_SECTIONS } from "./sections";

interface PanelHeaderProps {
  portfolioId: string;
}

/**
 * Cabecera del panel: marca, selector de cartera (un clic, mantiene `?p=`), enlaces a los
 * bloques y vuelta a la app. Un aviso `aria-live` dice qué cartera se está viendo al cambiarla.
 */
export function PanelHeader({ portfolioId }: PanelHeaderProps) {
  const [params] = useSearchParams();
  const { data } = usePortfolios();
  const name = data?.find((p) => p.id === portfolioId)?.name;
  const query = params.toString() ? `?${params.toString()}` : "";

  return (
    <header className="sticky top-0 z-10 border-b border-line bg-surface">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-8 gap-y-3 px-6 py-3">
        <span className="text-xl font-semibold text-accent">KAIROS</span>
        <div className="flex items-center gap-3">
          <span aria-hidden="true" className="text-base font-medium text-ink-muted">
            Cartera
          </span>
          <PortfolioPicker compact />
        </div>
        <nav aria-label="Bloques del panel" className="ml-auto flex flex-wrap items-center gap-1">
          {PANEL_SECTIONS.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="inline-flex min-h-touch items-center rounded-control px-3 text-base font-medium text-ink-muted no-underline hover:bg-surface-muted hover:text-ink"
            >
              {s.label}
            </a>
          ))}
          <Link
            to={`/inicio${query}`}
            className="inline-flex min-h-touch items-center px-3 text-base font-medium text-accent underline"
          >
            Volver a la app
          </Link>
        </nav>
      </div>
      <p role="status" aria-live="polite" className="sr-only">
        {name ? `Mostrando la cartera de ${name}` : ""}
      </p>
    </header>
  );
}
