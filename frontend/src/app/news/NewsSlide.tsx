import { Link } from "react-router";
import type { NewsItemOut } from "../../api/generated/schema";
import { ArrowRightIcon } from "../../components/icons";
import { NewsEffect } from "../news-feed/NewsEffect";

interface NewsSlideProps {
  news: NewsItemOut;
  position: number;
  total: number;
  direction: "next" | "prev";
  /** Destino de «Ver todas las noticias» (conserva `?p=`). */
  newsHref: string;
}

/**
 * Texto de una noticia (la portada y los controles los pinta NewsCarousel a la izquierda).
 * Patrón de carrusel de WAI-ARIA: role="group" + aria-roledescription="noticia" + "2 de 5".
 * El impacto es el de `NewsEffect` (el mismo de la pantalla Noticias): rango, estimado o medido,
 * confianza y «¿De dónde sale?». Todo viene del backend.
 */
export function NewsSlide({ news, position, total, direction, newsHref }: NewsSlideProps) {
  const summary = news.causal_chain.length > 0 ? news.causal_chain.join(" → ") : news.summary;
  return (
    <div
      role="group"
      aria-roledescription="noticia"
      aria-label={`${position} de ${total}`}
      data-calc-id={news.estimate?.calc_id ?? undefined}
      className={`h-full ${direction === "next" ? "motion-safe:animate-news-in-next" : "motion-safe:animate-news-in-prev"}`}
    >
      <div className="flex h-full min-w-0 flex-col gap-3">
        <h3 className="m-0 text-xl font-semibold leading-snug text-ink">{news.title}</h3>
        <p className="m-0 line-clamp-3 text-base text-ink-muted">{summary}</p>

        <div className="mt-1">
          <NewsEffect estimate={news.estimate} compact />
        </div>

        <div className="mt-auto flex flex-wrap items-center justify-between gap-x-4 gap-y-1 pt-2">
          <p className="m-0 text-sm text-ink-muted">Fuente: {news.source.label}</p>
          <Link
            to={newsHref}
            className="inline-flex min-h-touch items-center gap-1 font-semibold text-accent underline"
          >
            Ver todas las noticias
            <ArrowRightIcon className="size-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
