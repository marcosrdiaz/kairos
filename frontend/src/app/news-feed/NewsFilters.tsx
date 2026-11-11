import type { NewsCategory } from "../../api/generated/schema";
import type { NewsFilter } from "../../api/hooks/useNews";
import { CategoryIcon } from "./NewsCover";
import { CATEGORIES, CATEGORY_LABEL } from "./labels";

const CHIP =
  "inline-flex min-h-touch shrink-0 items-center gap-2 rounded-full border border-line bg-surface px-4 py-2 text-base font-medium whitespace-nowrap text-ink transition-colors hover:border-accent aria-pressed:border-accent aria-pressed:bg-accent aria-pressed:text-on-accent motion-reduce:transition-none";

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
  const pickCategory = (category: NewsCategory | null) => onChange({ ...filter, category });
  return (
    <div className="-mx-1 flex items-center gap-2 overflow-x-auto px-1 py-1 [scrollbar-width:thin]">
      <div role="group" aria-label="Qué noticias mostrar" className="flex shrink-0 gap-2">
        <button
          type="button"
          aria-pressed={filter.affecting}
          onClick={() => onChange({ ...filter, affecting: true })}
          className={CHIP}
        >
          Te afectan
        </button>
        <button
          type="button"
          aria-pressed={!filter.affecting}
          onClick={() => onChange({ ...filter, affecting: false })}
          className={CHIP}
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
          className={CHIP}
        >
          Todas las categorías
        </button>
        {CATEGORIES.map((category) => (
          <button
            key={category}
            type="button"
            aria-pressed={filter.category === category}
            onClick={() => pickCategory(category)}
            className={CHIP}
          >
            <CategoryIcon category={category} className="size-4" />
            {CATEGORY_LABEL[category]}
          </button>
        ))}
      </div>
    </div>
  );
}
