import { EmptyNote } from "../../components/PageTitle";
import { NewsCarousel } from "./NewsCarousel";
import { useEventNews } from "./useEventNews";

interface NewsSectionProps {
  portfolioId: string;
  /** Destino de "Ver en el panel" (conserva `?p=`). */
  panelHref: string;
}

function Header() {
  return (
    <>
      <h2 id="news-heading" className="m-0 mb-1 text-lg font-semibold text-ink">
        Noticias que afectan a tu cartera
      </h2>
      <p className="m-0 text-sm text-ink-muted">
        Solo lo que toca a tus fondos y acciones. El impacto es una estimación con rango.
      </p>
    </>
  );
}

/**
 * Resumen de noticias de Inicio (T2-19): eventos que afectan a la cartera, en carrusel.
 * Es la región etiquetada del patrón de carrusel (aria-roledescription="carrusel").
 */
export function NewsSection({ portfolioId, panelHref }: NewsSectionProps) {
  const { data, isPending, isError } = useEventNews(portfolioId);
  const hasNews = data !== undefined && data.length > 0;
  return (
    <section
      aria-roledescription="carrusel"
      aria-labelledby="news-heading"
      className="rounded-card border border-line bg-surface p-5 lg:p-6"
    >
      {hasNews ? (
        <NewsCarousel events={data} panelHref={panelHref} header={<Header />} />
      ) : (
        <div className="flex flex-col gap-4">
          <div>
            <Header />
          </div>
          {isPending && (
            <div
              role="status"
              aria-label="Cargando noticias"
              className="h-60 rounded-control bg-surface-muted motion-safe:animate-pulse"
            />
          )}
          {isError && (
            <EmptyNote>
              Ahora mismo no podemos cargar las noticias. Vuelve a intentarlo en un rato.
            </EmptyNote>
          )}
          {data && <EmptyNote>Estos días no ha pasado nada que afecte a tu cartera.</EmptyNote>}
        </div>
      )}
    </section>
  );
}
