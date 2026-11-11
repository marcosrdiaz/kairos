import { useEffect, useState, type FocusEvent, type ReactNode } from "react";
import { Link } from "react-router";
import type { NewsItemOut } from "../../api/generated/schema";
import { ArrowLeftIcon, ArrowRightIcon, PauseIcon, PlayIcon } from "../../components/icons";
import { NewsCover } from "../news-feed/NewsCover";
import { AUTO_ADVANCE_MS } from "./labels";
import { NewsSlide } from "./NewsSlide";

function prefersReducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function isKeyboardFocus(el: Element): boolean {
  try {
    return el.matches(":focus-visible");
  } catch {
    return false;
  }
}

const arrowButton =
  "inline-flex size-11 shrink-0 items-center justify-center rounded-full border border-line-strong bg-surface text-ink hover:bg-surface-muted";

interface NewsCarouselProps {
  items: NewsItemOut[];
  /** Destino de «Ver todas las noticias» (conserva `?p=`). */
  newsHref: string;
  /** Título de la sección: va en la misma fila que la pausa y el contador. */
  header?: ReactNode;
}

/**
 * Carrusel de noticias (patrón "auto-rotating carousel" de WAI-ARIA):
 * - Avanza solo cada 10 s hacia la siguiente noticia (entra por la derecha).
 * - Se detiene mientras el ratón está encima o el foco de teclado está dentro, y con el botón
 *   de pausa (WCAG 2.2.2). Con prefers-reduced-motion empieza en pausa.
 * - Mientras rota, la región no se anuncia (aria-live="off"); en pausa, sí ("polite").
 */
export function NewsCarousel({ items, newsHref, header }: NewsCarouselProps) {
  const total = items.length;
  const [rawIndex, setIndex] = useState(0);
  const [direction, setDirection] = useState<"next" | "prev">("next");
  const [paused, setPaused] = useState(prefersReducedMotion);
  const [hovered, setHovered] = useState(false);
  const [keyboardInside, setKeyboardInside] = useState(false);

  const index = total > 0 ? rawIndex % total : 0;
  const rotating = total > 1 && !paused && !hovered && !keyboardInside;

  const go = (to: number, dir: "next" | "prev") => {
    setDirection(dir);
    setIndex(((to % total) + total) % total);
  };

  useEffect(() => {
    if (!rotating) return;
    const t = setTimeout(() => {
      setDirection("next");
      setIndex((i) => (i + 1) % total);
    }, AUTO_ADVANCE_MS);
    return () => clearTimeout(t);
  }, [rotating, index, total]);

  const onFocus = (e: FocusEvent<HTMLElement>) => {
    if (isKeyboardFocus(e.target)) setKeyboardInside(true);
  };
  const onBlur = (e: FocusEvent<HTMLElement>) => {
    if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setKeyboardInside(false);
  };

  const current = items[index];
  if (!current) return null;

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={onFocus}
      onBlur={onBlur}
      className="grid gap-2 md:grid-cols-[15rem_minmax(0,1fr)] md:grid-rows-[auto_1fr] md:gap-x-4 md:gap-y-2"
    >
      {/* Título a la izquierda; contador, flechas, pausa y enlace a la derecha. En escritorio va en
          la columna derecha, a la derecha de la imagen. */}
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 md:col-start-2 md:row-start-1 md:pr-3 md:pt-2.5 lg:flex-nowrap">
        <div className="min-w-0">{header}</div>
        <div className="flex max-w-full flex-wrap items-center gap-x-2 gap-y-1 lg:shrink-0">
          {total > 1 && (
            <>
              <p className="m-0 text-sm text-ink-muted" aria-hidden="true">
                {index + 1} / {total}
              </p>
              <button
                type="button"
                onClick={() => go(index - 1, "prev")}
                className={arrowButton}
                aria-label="Noticia anterior"
                aria-controls="news-slides"
              >
                <ArrowLeftIcon className="size-5" />
              </button>
              <button
                type="button"
                onClick={() => go(index + 1, "next")}
                className={arrowButton}
                aria-label="Noticia siguiente"
                aria-controls="news-slides"
              >
                <ArrowRightIcon className="size-5" />
              </button>
              <button
                type="button"
                onClick={() => setPaused((p) => !p)}
                className={arrowButton}
                aria-label={paused ? "Reanudar el pase automático" : "Pausar el pase automático"}
              >
                {paused ? <PlayIcon className="size-5" /> : <PauseIcon className="size-5" />}
              </button>
            </>
          )}
          <Link
            to={newsHref}
            aria-label="Ver todas las noticias"
            className="inline-flex min-h-touch items-center gap-1 pl-2 text-sm font-semibold text-accent underline"
          >
            Ver todas
            <ArrowRightIcon className="size-4" />
          </Link>
        </div>
      </div>

      {/* La imagen, casi a los bordes de la tarjeta y a toda su altura (escritorio); en móvil, entre la
          cabecera y el texto. */}
      <div className="relative min-h-28 overflow-hidden rounded-control md:col-start-1 md:row-span-2 md:row-start-1 md:min-h-0">
        <div
          key={current.id}
          className={`absolute inset-0 ${direction === "next" ? "motion-safe:animate-news-in-next" : "motion-safe:animate-news-in-prev"}`}
        >
          <NewsCover category={current.category} publishedAt={current.published_at} dense />
        </div>
      </div>

      <div
        id="news-slides"
        aria-live={rotating ? "off" : "polite"}
        className="min-w-0 md:col-start-2 md:row-start-2 md:pb-2.5 md:pr-3"
      >
        <NewsSlide
          key={current.id}
          news={current}
          position={index + 1}
          total={total}
          direction={direction}
        />
      </div>
    </div>
  );
}
