import { useEffect, useState, type FocusEvent, type ReactNode } from "react";
import type { EventImpactOut } from "../../api/generated/schema";
import { ArrowLeftIcon, ArrowRightIcon, PauseIcon, PlayIcon } from "../../components/icons";
import { EventArt } from "./EventArt";
import { AUTO_ADVANCE_MS } from "./labels";
import { NewsSlide, type PageFlip } from "./NewsSlide";
import "./news.css";

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

/** Flechas sobre la imagen: centradas en vertical, fondo de superficie para que contrasten. */
const overlayButton = `${arrowButton} absolute top-1/2 -translate-y-1/2`;

interface NewsCarouselProps {
  events: EventImpactOut[];
  panelHref: string;
  /** Título de la sección: va en la misma fila que la pausa y el contador. */
  header?: ReactNode;
}

/**
 * Carrusel de noticias (patrón "auto-rotating carousel" de WAI-ARIA):
 * - Avanza solo cada 10 s hacia la siguiente noticia. Cada cambio pasa como una hoja de
 *   calendario: baja de arriba abajo, o sube al retroceder (news.css). Al cargar no anima.
 * - Se detiene mientras el ratón está encima o el foco de teclado está dentro, y con el botón
 *   de pausa (WCAG 2.2.2). Con prefers-reduced-motion empieza en pausa.
 * - Mientras rota, la región no se anuncia (aria-live="off"); en pausa, sí ("polite").
 */
export function NewsCarousel({ events, panelHref, header }: NewsCarouselProps) {
  const total = events.length;
  const [rawIndex, setIndex] = useState(0);
  const [flip, setFlip] = useState<PageFlip | undefined>(undefined);
  const [paused, setPaused] = useState(prefersReducedMotion);
  const [hovered, setHovered] = useState(false);
  const [keyboardInside, setKeyboardInside] = useState(false);

  const index = total > 0 ? rawIndex % total : 0;
  const rotating = total > 1 && !paused && !hovered && !keyboardInside;

  const go = (to: number, dir: PageFlip) => {
    setFlip(dir);
    setIndex(((to % total) + total) % total);
  };

  useEffect(() => {
    if (!rotating) return;
    const t = setTimeout(() => {
      setFlip("down");
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

      {/* Imagen con los controles encima (galería) a la izquierda; texto a la derecha. */}
      <div className="grid gap-5 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] md:gap-8">
        <div className="news-stage relative aspect-4/3 overflow-hidden rounded-control md:aspect-auto md:min-h-64">
          <div
            key={current.event_id}
            data-flip={flip}
            className="news-page absolute inset-0"
          >
            <EventArt type={current.event_type} />
          </div>
          {total > 1 && (
            <>
              <button
                type="button"
                onClick={() => go(index - 1, "up")}
                className={`${overlayButton} left-3`}
                aria-label="Noticia anterior"
                aria-controls="news-slides"
              >
                <ArrowLeftIcon className="size-5" />
              </button>
              <button
                type="button"
                onClick={() => go(index + 1, "down")}
                className={`${overlayButton} right-3`}
                aria-label="Noticia siguiente"
                aria-controls="news-slides"
              >
                <ArrowRightIcon className="size-5" />
              </button>
              <ul className="absolute bottom-3 left-1/2 m-0 flex -translate-x-1/2 list-none items-center gap-0.5 rounded-full bg-surface/90 px-1.5 py-0.5">
                {events.map((e, i) => (
                  <li key={e.event_id} className="flex">
                    <button
                      type="button"
                      onClick={() => go(i, i < index ? "up" : "down")}
                      aria-label={`Noticia ${i + 1}: ${e.title}`}
                      aria-current={i === index ? "true" : undefined}
                      className="group inline-flex size-6 items-center justify-center rounded-full"
                    >
                      <span
                        className={`block h-2 rounded-full transition-all ${i === index ? "w-4 bg-accent" : "w-2 bg-line-strong group-hover:bg-ink-muted"}`}
                      />
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>

        <div
          id="news-slides"
          aria-live={rotating ? "off" : "polite"}
          className="news-stage min-w-0"
        >
          <NewsSlide
            key={current.event_id}
            event={current}
            position={index + 1}
            total={total}
            flip={flip}
            panelHref={panelHref}
          />
        </div>
      </div>
    </div>
  );
}
