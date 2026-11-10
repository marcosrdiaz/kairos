import type { NewsCategory } from "../../api/generated/schema";
import type { NewsFilter } from "../../api/hooks/useNews";
import { CATEGORIES, CATEGORY_LABEL } from "./labels";

const CHIP =
  "min-h-touch rounded-full border border-line bg-surface px-4 py-2 text-base font-medium text-ink transition-colors hover:border-accent aria-pressed:border-accent aria-pressed:bg-accent aria-pressed:text-on-accent motion-reduce:transition-none";

interface NewsFiltersProps {
  filter: NewsFilter;
  onChange: (filter: NewsFilter) => void;
}

/**
 * Filtros de la pantalla Noticias: «Te afectan» / «Todas» y una categoría (o ninguna). Botones
 * con `aria-pressed` dentro de grupos con nombre, como los escenarios del panel.
 */
export function NewsFilters({ filter, onChange }: NewsFiltersProps) {
  const pickCategory = (category: NewsCategory | null) => onChange({ ...filter, category });
  return (
    <div className="flex flex-col gap-3">
      <div role="group" aria-label="Qué noticias mostrar" className="flex flex-wrap gap-2">
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
      <div role="group" aria-label="Categoría" className="flex flex-wrap gap-2">
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
            {CATEGORY_LABEL[category]}
          </button>
        ))}
      </div>
    </div>
  );
}
