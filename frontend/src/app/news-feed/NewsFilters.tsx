import { useEffect, useId, useRef, useState } from "react";
import type { NewsCategory } from "../../api/generated/schema";
import type { NewsFilter } from "../../api/hooks/useNews";
import { ArrowLeftIcon, ArrowRightIcon } from "../../components/icons";
import { CategoryIcon } from "./NewsCover";
import { CATEGORIES, CATEGORY_LABEL } from "./labels";

const BASE_CHIP =
  "inline-flex min-h-touch shrink-0 items-center gap-2 rounded-full border border-line bg-surface px-4 py-2 text-base font-medium whitespace-nowrap text-ink transition-colors hover:border-accent focus-visible:outline-focus motion-reduce:transition-none";
const FILTER_CHIP = `${BASE_CHIP} aria-pressed:border-accent aria-pressed:bg-accent aria-pressed:text-on-accent`;
const CATEGORY_TONE: Record<NewsCategory, { icon: string; selected: string }> = {
  company: {
    icon: "text-icon-blue",
    selected: "aria-pressed:bg-icon-blue-bg aria-pressed:text-icon-blue",
  },
  earnings: {
    icon: "text-icon-purple",
    selected: "aria-pressed:bg-icon-purple-bg aria-pressed:text-icon-purple",
  },
  central_bank: {
    icon: "text-icon-gold",
    selected: "aria-pressed:bg-icon-gold-bg aria-pressed:text-icon-gold",
  },
  politics: {
    icon: "text-icon-red",
    selected: "aria-pressed:bg-icon-red-bg aria-pressed:text-icon-red",
  },
  commodities: {
    icon: "text-icon-gold",
    selected: "aria-pressed:bg-icon-gold-bg aria-pressed:text-icon-gold",
  },
  fx: {
    icon: "text-icon-green",
    selected: "aria-pressed:bg-icon-green-bg aria-pressed:text-icon-green",
  },
  other: {
    icon: "text-nodata",
    selected: "aria-pressed:bg-nodata-bg aria-pressed:text-nodata",
  },
};

const SCROLL_BUTTON =
  "grid size-touch shrink-0 place-items-center rounded-full border border-line-strong bg-surface text-ink transition-colors hover:border-accent disabled:cursor-not-allowed disabled:opacity-40 motion-reduce:transition-none";

interface NewsFiltersProps {
  filter: NewsFilter;
  onChange: (filter: NewsFilter) => void;
}

/**
 * Filtros de la pantalla Noticias (T5-17): una sola línea de chips, «Te afectan» / «Todas» y
 * luego las categorías con su icono. Botones con `aria-pressed` en grupos con nombre; en móvil la
 * línea se desplaza en horizontal en lugar de partirse.
 */
export function NewsFilters({ filter, onChange }: NewsFiltersProps) {
  const railRef = useRef<HTMLDivElement>(null);
  const railId = useId();
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);
  const pickCategory = (category: NewsCategory | null) => onChange({ ...filter, category });

  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;

    const syncScrollButtons = () => {
      const maxScroll = rail.scrollWidth - rail.clientWidth;
      setCanScrollLeft(rail.scrollLeft > 1);
      setCanScrollRight(maxScroll > 1 && rail.scrollLeft < maxScroll - 1);
    };

    syncScrollButtons();
    rail.addEventListener("scroll", syncScrollButtons, { passive: true });
    window.addEventListener("resize", syncScrollButtons);
    const resizeObserver =
      typeof ResizeObserver === "undefined" ? null : new ResizeObserver(syncScrollButtons);
    resizeObserver?.observe(rail);

    return () => {
      rail.removeEventListener("scroll", syncScrollButtons);
      window.removeEventListener("resize", syncScrollButtons);
      resizeObserver?.disconnect();
    };
  }, []);

  const scrollCategories = (direction: -1 | 1) => {
    const rail = railRef.current;
    if (!rail) return;
    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    rail.scrollBy({
      left: direction * Math.max(180, Math.round(rail.clientWidth * 0.72)),
      behavior: reducedMotion ? "auto" : "smooth",
    });
  };

  return (
    <div className="flex min-w-0 items-center gap-2">
      <button
        type="button"
        aria-label="Desplazar categorías a la izquierda"
        aria-controls={railId}
        disabled={!canScrollLeft}
        onClick={() => scrollCategories(-1)}
        className={SCROLL_BUTTON}
      >
        <ArrowLeftIcon className="size-5" />
      </button>
        <div
          id={railId}
          ref={railRef}
          role="region"
          aria-label="Categorías de noticias"
          tabIndex={0}
          className="news-filter-rail flex min-w-0 flex-1 items-center gap-2 overflow-x-auto py-1"
        >
          <div role="group" aria-label="Qué noticias mostrar" className="flex shrink-0 gap-2">
            <button
              type="button"
              aria-pressed={filter.affecting}
              onClick={() => onChange({ ...filter, affecting: true })}
              className={FILTER_CHIP}
            >
              Te afectan
            </button>
            <button
              type="button"
              aria-pressed={!filter.affecting}
              onClick={() => onChange({ ...filter, affecting: false })}
              className={FILTER_CHIP}
            >
              Todas
            </button>
          </div>
          <span aria-hidden="true" className="mx-1 h-6 w-px shrink-0 bg-line" />
          <div role="group" aria-label="Categoría" className="flex shrink-0 gap-2">
            <button
              type="button"
              aria-pressed={filter.category === null}
              onClick={() => pickCategory(null)}
              className={FILTER_CHIP}
            >
              Todas las categorías
            </button>
            {CATEGORIES.map((category) => {
            const tone = CATEGORY_TONE[category];
            return (
                <button
                  key={category}
                  type="button"
                  aria-pressed={filter.category === category}
                  onClick={() => pickCategory(category)}
                  className={`${BASE_CHIP} ${tone.selected}`}
                >
                  <CategoryIcon category={category} className={`size-4 ${tone.icon}`} />
                  {CATEGORY_LABEL[category]}
                </button>
            );
            })}
          </div>
        </div>
      <button
        type="button"
        aria-label="Desplazar categorías a la derecha"
        aria-controls={railId}
        disabled={!canScrollRight}
        onClick={() => scrollCategories(1)}
        className={SCROLL_BUTTON}
      >
        <ArrowRightIcon className="size-5" />
      </button>
    </div>
  );
}
