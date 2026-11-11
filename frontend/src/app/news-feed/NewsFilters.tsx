import { useEffect, useId, useRef, useState } from "react";
import type { NewsCategory } from "../../api/generated/schema";
import type { NewsFilter } from "../../api/hooks/useNews";
import { ArrowLeftIcon, ArrowRightIcon, CalendarIcon } from "../../components/icons";
import { CategoryIcon } from "./NewsCover";
import { CATEGORIES, CATEGORY_LABEL } from "./labels";

const BASE_CHIP =
  "inline-flex min-h-touch shrink-0 items-center gap-2 rounded-full border border-line bg-surface px-4 py-2 text-base font-medium whitespace-nowrap text-ink transition-colors hover:border-accent focus-visible:outline-focus motion-reduce:transition-none";
const FILTER_CHIP = `${BASE_CHIP} aria-pressed:border-accent aria-pressed:bg-accent aria-pressed:text-on-accent`;
const ICON_BADGE =
  "grid size-6 shrink-0 place-items-center rounded-full bg-icon-contrast-bg text-white";

const SCROLL_BUTTON =
  "grid size-touch shrink-0 place-items-center rounded-full border border-line-strong bg-surface text-ink transition-colors hover:border-accent disabled:cursor-not-allowed disabled:opacity-40 motion-reduce:transition-none";

export interface NewsDateRange {
  from: string;
  to: string;
}

interface NewsFiltersProps {
  filter: NewsFilter;
  onChange: (filter: NewsFilter) => void;
  dateRange: NewsDateRange;
  onDateRangeChange: (dateRange: NewsDateRange) => void;
}

/**
 * Filtros de la pantalla Noticias (T5-17): una sola línea de chips, «Te afectan» / «Todas» y
 * el filtro de fechas, alcance y categorías. Botones con `aria-pressed` en grupos con nombre; en
 * móvil la línea se desplaza en horizontal en lugar de partirse.
 */
export function NewsFilters({
  filter,
  onChange,
  dateRange,
  onDateRangeChange,
}: NewsFiltersProps) {
  const railRef = useRef<HTMLDivElement>(null);
  const railId = useId();
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);
  const [showDateFilter, setShowDateFilter] = useState(false);
  const dateFilterId = `${railId}-date-filter`;
  const hasDateRange = Boolean(dateRange.from || dateRange.to);
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
    <div className="flex min-w-0 flex-col gap-3">
      <div className="flex min-w-0 items-center gap-2">
        <button
          type="button"
          aria-label="Desplazar filtros a la izquierda"
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
          aria-label="Filtros de noticias"
          tabIndex={0}
          className="news-filter-rail flex min-w-0 flex-1 items-center gap-2 overflow-x-auto py-1"
        >
          <button
            type="button"
            aria-expanded={showDateFilter}
            aria-controls={showDateFilter ? dateFilterId : undefined}
            onClick={() => setShowDateFilter((open) => !open)}
            className={`${BASE_CHIP} ${hasDateRange ? "border-accent bg-accent text-on-accent" : ""}`}
          >
            <span className={ICON_BADGE}>
              <CalendarIcon className="size-4" />
            </span>
            {hasDateRange ? "Fechas activas" : "Fecha"}
          </button>
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
            {CATEGORIES.map((category) => (
              <button
                key={category}
                type="button"
                aria-pressed={filter.category === category}
                onClick={() => pickCategory(category)}
                className={FILTER_CHIP}
              >
                <span className={ICON_BADGE}>
                  <CategoryIcon category={category} className="size-4 text-white" />
                </span>
                {CATEGORY_LABEL[category]}
              </button>
            ))}
          </div>
        </div>
        <button
          type="button"
          aria-label="Desplazar filtros a la derecha"
          aria-controls={railId}
          disabled={!canScrollRight}
          onClick={() => scrollCategories(1)}
          className={SCROLL_BUTTON}
        >
          <ArrowRightIcon className="size-5" />
        </button>
      </div>
      {showDateFilter && (
        <div
          id={dateFilterId}
          className="flex flex-wrap items-end gap-3 rounded-card border border-line bg-surface p-4"
        >
          <label className="flex min-w-36 flex-1 flex-col gap-1 text-sm font-medium text-ink">
            Desde
            <input
              type="date"
              value={dateRange.from}
              max={dateRange.to || undefined}
              onChange={(event) => {
                const from = event.target.value;
                onDateRangeChange({
                  from,
                  to: dateRange.to && from > dateRange.to ? from : dateRange.to,
                });
              }}
              className="min-h-touch rounded-control border border-line-strong bg-surface px-3 text-base text-ink focus-visible:outline-focus"
            />
          </label>
          <label className="flex min-w-36 flex-1 flex-col gap-1 text-sm font-medium text-ink">
            Hasta
            <input
              type="date"
              value={dateRange.to}
              min={dateRange.from || undefined}
              onChange={(event) => {
                const to = event.target.value;
                onDateRangeChange({
                  from: dateRange.from && to < dateRange.from ? to : dateRange.from,
                  to,
                });
              }}
              className="min-h-touch rounded-control border border-line-strong bg-surface px-3 text-base text-ink focus-visible:outline-focus"
            />
          </label>
          {hasDateRange && (
            <button
              type="button"
              onClick={() => onDateRangeChange({ from: "", to: "" })}
              className="min-h-touch rounded-full px-3 text-base font-semibold text-ink-muted underline decoration-line-strong underline-offset-4 hover:text-ink focus-visible:outline-focus"
            >
              Limpiar fechas
            </button>
          )}
        </div>
      )}
    </div>
  );
}
