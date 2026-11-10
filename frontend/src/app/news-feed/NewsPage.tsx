import { useState } from "react";
import { useNews, type NewsFilter } from "../../api/hooks/useNews";
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
  const [filter, setFilter] = useState<NewsFilter>(DEFAULT_FILTER);
  const { data, isPending, isError } = useNews(portfolioId, filter);

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
        </section>
        <PanelNotice />
      </div>
    </>
  );
}
