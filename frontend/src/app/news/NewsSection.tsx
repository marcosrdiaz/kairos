import { Link } from "react-router";
import { EmptyNote } from "../../components/PageTitle";
import { NewsCarousel } from "./NewsCarousel";
import { TOP_NEWS } from "./topNews";
import { useTopNews } from "./useTopNews";

interface NewsSectionProps {
  portfolioId: string;
  /** Destino de «Ver todas las noticias» (conserva `?p=`). */
  newsHref: string;
}

function Header() {
  return (
    <>
      <h2 id="news-heading" className="m-0 text-base font-semibold leading-snug text-ink">
        Lo que más mueve tu cartera hoy
      </h2>
      <p className="m-0 line-clamp-2 text-xs leading-snug text-ink-muted">
        Las {TOP_NEWS} noticias de las últimas 24 horas con más impacto en tu cartera. Impacto
        estimado, con rango.
      </p>
    </>
  );
}

/**
 * Resumen de noticias de Inicio (T2-19, TD-04): las noticias reales de las últimas 24 horas que
 * más mueven la cartera, en carrusel. Es la región etiquetada del patrón de carrusel
 * (aria-roledescription="carrusel").
 */
export function NewsSection({ portfolioId, newsHref }: NewsSectionProps) {
  const { data, isPending, isError } = useTopNews(portfolioId);
  const hasNews = data !== undefined && data.length > 0;
  return (
    <section
      aria-roledescription="carrusel"
      aria-labelledby="news-heading"
      className="rounded-card border border-line bg-surface p-4"
    >
      {hasNews ? (
        <NewsCarousel items={data} newsHref={newsHref} header={<Header />} />
      ) : (
        <div className="flex flex-col gap-4">
          <div>
            <Header />
          </div>
          {isPending && (
            <div
              role="status"
              aria-label="Cargando noticias"
              className="h-32 rounded-control bg-surface-muted motion-safe:animate-pulse"
            />
          )}
          {isError && !data && (
            <EmptyNote>
              Ahora mismo no podemos cargar las noticias. Vuelve a intentarlo en un rato.
            </EmptyNote>
          )}
          {data && (
            <EmptyNote>
              En las últimas 24 horas no ha salido ninguna noticia que mueva tu cartera.{" "}
              <Link to={newsHref} className="font-semibold text-accent underline">
                Ver todas las noticias
              </Link>
            </EmptyNote>
          )}
        </div>
      )}
    </section>
  );
}
