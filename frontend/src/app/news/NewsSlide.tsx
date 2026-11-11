import type { NewsItemOut } from "../../api/generated/schema";
import { NewsMeta } from "../news-feed/NewsCover";
import { NewsEffect } from "../news-feed/NewsEffect";

interface NewsSlideProps {
  news: NewsItemOut;
  position: number;
  total: number;
  direction: "next" | "prev";
}

/**
 * Texto de una noticia (la portada y los controles los pinta NewsCarousel a la izquierda).
 * Patrón de carrusel de WAI-ARIA: role="group" + aria-roledescription="noticia" + "2 de 5".
 * Todo el texto va aquí: categoría y fecha, título, resumen, etiquetas y el impacto con su rango, y
 * «Fuente» abajo a la derecha (en la línea del impacto si cabe). «Ver todas las noticias» lo pinta
 * NewsCarousel en su cabecera. El impacto es el de `NewsEffect` (el mismo de la pantalla Noticias):
 * rango, estimado o medido, confianza y «¿De dónde sale?». Todo viene del backend.
 */
export function NewsSlide({ news, position, total, direction }: NewsSlideProps) {
  const summary = news.causal_chain.length > 0 ? news.causal_chain.join(" → ") : news.summary;
  return (
    <div
      role="group"
      aria-roledescription="noticia"
      aria-label={`${position} de ${total}`}
      data-calc-id={news.estimate?.calc_id ?? undefined}
      className={`h-full ${direction === "next" ? "motion-safe:animate-news-in-next" : "motion-safe:animate-news-in-prev"}`}
    >
      <div className="flex h-full min-w-0 flex-col gap-1.5">
        <NewsMeta category={news.category} publishedAt={news.published_at} />
        <h3 className="m-0 line-clamp-2 text-lg font-semibold leading-snug text-ink">{news.title}</h3>
        <p className="m-0 line-clamp-1 text-sm text-ink-muted">{summary}</p>
        <div className="mt-auto flex flex-wrap items-end justify-between gap-x-4 gap-y-1">
          <NewsEffect estimate={news.estimate} compact />
          {/* A la derecha; en escritorio estrecho deja hueco al botón flotante del asistente. */}
          <p className="m-0 ml-auto max-w-full truncate text-sm text-ink-muted lg:mr-24 2xl:mr-0">
            Fuente: {news.source.label}
          </p>
        </div>
      </div>
    </div>
  );
}
