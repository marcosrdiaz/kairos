import { useState } from "react";
import { NEWS_MAX, NEWS_PAGE, useNews, type NewsFilter } from "../../api/hooks/useNews";
import { EmptyNote, PageTitle } from "../../components/PageTitle";
import { PanelNotice } from "../../components/notices/Notices";
import { usePortfolioId } from "../portfolio-picker/usePortfolioId";
import { NewsCard } from "./NewsCard";
import { NewsFilters } from "./NewsFilters";
import { CATEGORY_LABEL } from "./labels";

const DEFAULT_FILTER: NewsFilter = { category: null, affecting: true };

function emptyText(filter: NewsFilter): string {
  const scope = filter.category ? ` de ${CATEGORY_LABEL[filter.category].toLowerCase()}` : "";
  return filter.affecting
    ? `Ahora mismo no hay noticias${scope} que afecten a esta cartera.`
    : `Ahora mismo no hay noticias${scope}.`;
}

/**
 * Sección Noticias (T4-32): las noticias que afectan a la cartera elegida, con lo que pueden
 * significar para ella. Por defecto solo «Te afectan»; se puede ver todas y filtrar por tipo.
 */
export function NewsPage() {
  const [portfolioId] = usePortfolioId();
  const [filter, setFilterState] = useState<NewsFilter>(DEFAULT_FILTER);
  const [limit, setLimit] = useState(NEWS_PAGE);
  const { data, isPending, isError, isFetching } = useNews(portfolioId, filter, limit);
  const setFilter = (next: NewsFilter) => {
    setFilterState(next);
    setLimit(NEWS_PAGE);
  };
  const canLoadMore = data !== undefined && data.length >= limit && limit < NEWS_MAX;

  return (
    <>
      <PageTitle>Noticias</PageTitle>
      <div className="flex max-w-3xl flex-col gap-6">
        <p className="m-0 text-base text-ink-muted">
          Lo que pasa en los mercados, traducido a tu cartera: cuánto podría moverla cada noticia,
          en qué plazo y desde cuándo se nota en cada posición.
        </p>
        <NewsFilters filter={filter} onChange={setFilter} />
        <section aria-labelledby="news-list-title" aria-busy={isPending} className="flex flex-col gap-4">
          <h2 id="news-list-title" className="sr-only">
            Lista de noticias
          </h2>
          {isPending && (
            <p className="m-0 text-base text-ink-muted" role="status">
              Cargando noticias…
            </p>
          )}
          {isError && !data && (
            <EmptyNote>
              Ahora mismo no podemos mostrar las noticias. Vuelve a intentarlo en unos segundos.
            </EmptyNote>
          )}
          {data?.length === 0 && <EmptyNote>{emptyText(filter)}</EmptyNote>}
          {data?.map((item) => <NewsCard key={item.id} item={item} />)}
          {canLoadMore && (
            <button
              type="button"
              onClick={() => setLimit((n) => Math.min(n + NEWS_PAGE, NEWS_MAX))}
              disabled={isFetching}
              className="min-h-touch self-center rounded-full border border-line bg-surface px-5 py-2 text-base font-semibold text-ink transition-colors hover:border-accent disabled:opacity-60 motion-reduce:transition-none"
            >
              {isFetching ? "Cargando…" : "Ver más noticias"}
            </button>
          )}
        </section>
        <PanelNotice />
      </div>
    </>
  );
}
