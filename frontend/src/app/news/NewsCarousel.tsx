import { useEffect, useState, type FocusEvent, type ReactNode } from "react";
import type { EventImpactOut } from "../../api/generated/schema";
import { ArrowLeftIcon, ArrowRightIcon, PauseIcon, PlayIcon } from "../../components/icons";
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
  events: EventImpactOut[];
  panelHref: string;
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
export function NewsCarousel({ events, panelHref, header }: NewsCarouselProps) {
  const total = events.length;
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

  const current = events[index];
  if (!current) return null;

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={onFocus}
      onBlur={onBlur}
      className="flex flex-col gap-4"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">{header}</div>
        {total > 1 && (
          <div className="flex shrink-0 items-center gap-3">
            <p className="m-0 text-sm text-ink-muted" aria-hidden="true">
              {index + 1} / {total}
            </p>
            <button
              type="button"
              onClick={() => setPaused((p) => !p)}
              className={arrowButton}
              aria-label={paused ? "Reanudar el pase automático" : "Pausar el pase automático"}
            >
              {paused ? <PlayIcon className="size-5" /> : <PauseIcon className="size-5" />}
            </button>
          </div>
        )}
      </div>

      {/* Móvil: noticia arriba y flechas + puntos debajo. Escritorio: flechas a los lados. */}
      <div className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-x-2 gap-y-3 [grid-template-areas:'slide_slide_slide'_'prev_dots_next'] md:gap-x-4 md:[grid-template-areas:'prev_slide_next'_'._dots_.']">
        {total > 1 && (
          <button
            type="button"
            onClick={() => go(index - 1, "prev")}
            className={`${arrowButton} [grid-area:prev]`}
            aria-label="Noticia anterior"
            aria-controls="news-slides"
          >
            <ArrowLeftIcon className="size-5" />
          </button>
        )}
        <div
          id="news-slides"
          aria-live={rotating ? "off" : "polite"}
          className="min-w-0 overflow-hidden [grid-area:slide]"
        >
          <NewsSlide
            key={current.event_id}
            event={current}
            position={index + 1}
            total={total}
            direction={direction}
            panelHref={panelHref}
          />
        </div>
        {total > 1 && (
          <button
            type="button"
            onClick={() => go(index + 1, "next")}
            className={`${arrowButton} [grid-area:next]`}
            aria-label="Noticia siguiente"
            aria-controls="news-slides"
          >
            <ArrowRightIcon className="size-5" />
          </button>
        )}
        {total > 1 && (
          <ul className="m-0 flex list-none justify-center gap-1 p-0 [grid-area:dots]">
            {events.map((e, i) => (
              <li key={e.event_id}>
                <button
                  type="button"
                  onClick={() => go(i, i < index ? "prev" : "next")}
                  aria-label={`Noticia ${i + 1}: ${e.title}`}
                  aria-current={i === index ? "true" : undefined}
                  className="group inline-flex size-11 items-center justify-center rounded-full"
                >
                  <span
                    className={`block h-2.5 rounded-full transition-all ${i === index ? "w-6 bg-accent" : "w-2.5 bg-line-strong group-hover:bg-ink-muted"}`}
                  />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
