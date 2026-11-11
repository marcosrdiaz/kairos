import { useRef, useState } from "react";
import { NEWS_MAX, NEWS_PAGE, useNews, type NewsFilter } from "../../api/hooks/useNews";
import { EmptyNote, PageTitle } from "../../components/PageTitle";
import { usePortfolioId } from "../portfolio-picker/usePortfolioId";
import { NewsCard } from "./NewsCard";
import { NewsDetail } from "./NewsDetail";
import { NewsFilters, type NewsDateRange } from "./NewsFilters";
import { CATEGORY_LABEL } from "./labels";
import "./news-feed.css";

const DEFAULT_FILTER: NewsFilter = { category: null, affecting: true };
const MADRID_DATE = new Intl.DateTimeFormat("en-CA", {
  day: "2-digit",
  month: "2-digit",
  timeZone: "Europe/Madrid",
  year: "numeric",
});

function publishedDate(isoDate: string): string {
  const parts = MADRID_DATE.formatToParts(new Date(isoDate));
  const year = parts.find((part) => part.type === "year")?.value;
  const month = parts.find((part) => part.type === "month")?.value;
  const day = parts.find((part) => part.type === "day")?.value;
  if (!year || !month || !day) throw new Error("No se pudo interpretar la fecha de la noticia.");
  return `${year}-${month}-${day}`;
}

function emptyText(filter: NewsFilter, hasDateRange: boolean): string {
  if (hasDateRange) return "No hay noticias para las fechas seleccionadas.";
  const scope = filter.category ? ` de ${CATEGORY_LABEL[filter.category].toLowerCase()}` : "";
  return filter.affecting
    ? `Ahora mismo no hay noticias${scope} que afecten a esta cartera.`
    : `Ahora mismo no hay noticias${scope}.`;
}

/**
 * Sección Noticias (T4-32, rediseñada en T5-17): cards en dos columnas (una en pantallas
 * estrechas) con lo que cada noticia puede significar para la cartera elegida; al pulsar una,
 * el detalle se abre sobre el contenido. Por defecto solo «Te afectan»; se puede ver todas y
 * filtrar por tipo. Al final, el aviso «No es asesoramiento» como párrafo.
 */
export function NewsPage() {
  const [portfolioId] = usePortfolioId();
  const [filter, setFilterState] = useState<NewsFilter>(DEFAULT_FILTER);
  const [limit, setLimit] = useState(NEWS_PAGE);
  const [dateRange, setDateRange] = useState<NewsDateRange>({ from: "", to: "" });
  const [openId, setOpenId] = useState<string | null>(null);
  const opener = useRef<HTMLButtonElement | null>(null);
  const hasDateRange = Boolean(dateRange.from || dateRange.to);
  const requestLimit = hasDateRange ? NEWS_MAX : limit;
  const { data, isPending, isError, isFetching } = useNews(portfolioId, filter, requestLimit);
  const setFilter = (next: NewsFilter) => {
    setFilterState(next);
    setLimit(NEWS_PAGE);
  };
  const setDates = (next: NewsDateRange) => {
    setDateRange(next);
    setLimit(NEWS_PAGE);
  };
  const visibleNews = data?.filter((item) => {
    const date = publishedDate(item.published_at);
    return (!dateRange.from || date >= dateRange.from) && (!dateRange.to || date <= dateRange.to);
  });
  const canLoadMore =
    data !== undefined && data.length >= requestLimit && requestLimit < NEWS_MAX;
  const open = data?.find((n) => n.id === openId) ?? null;

  const openDetail = (id: string, button: HTMLButtonElement) => {
    opener.current = button;
    setOpenId(id);
  };
  const closeDetail = () => {
    setOpenId(null);
    // Tras quitar `inert` del <main> (al desmontar el detalle), el foco vuelve a la card.
    requestAnimationFrame(() => opener.current?.focus());
  };

  return (
    <>
      <PageTitle>Noticias</PageTitle>
      <div className="news-page-layout flex min-w-0 w-full flex-col gap-6">
        <p className="m-0 max-w-[65ch] text-base text-ink-muted">
          Lo que pasa en los mercados, traducido a tu cartera: cuánto podría moverla cada noticia,
          en qué plazo y desde cuándo se nota en cada posición.
        </p>
        <NewsFilters
          filter={filter}
          onChange={setFilter}
          dateRange={dateRange}
          onDateRangeChange={setDates}
        />
        <section
          aria-labelledby="news-list-title"
          aria-busy={isPending || isFetching}
          className="flex min-w-0 flex-col gap-4"
        >
          <h2 id="news-list-title" className="sr-only">
            Lista de noticias
          </h2>
          {isPending && (
            <p className="m-0 text-base text-ink-muted" role="status">
              Cargando noticias…
            </p>
          )}
          {visibleNews?.length === 0 && isFetching && (
            <p className="m-0 text-base text-ink-muted" role="status">
              Buscando noticias…
            </p>
          )}
          {isError && !data && (
            <EmptyNote>
              Ahora mismo no podemos mostrar las noticias. Vuelve a intentarlo en unos segundos.
            </EmptyNote>
          )}
          {visibleNews?.length === 0 && !isFetching && (
            <EmptyNote>{emptyText(filter, hasDateRange)}</EmptyNote>
          )}
          {visibleNews && visibleNews.length > 0 && (
            <div className="grid min-w-0 grid-cols-1 gap-5 @3xl/app-content:grid-cols-2">
              {visibleNews.map((item) => (
                <NewsCard key={item.id} item={item} onOpen={openDetail} />
              ))}
            </div>
          )}
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
        <p className="m-0 max-w-[65ch] text-sm text-ink-muted">
          <strong className="font-semibold text-ink">No es asesoramiento.</strong> Kairos explica
          con contexto cómo podría afectar cada noticia a tu cartera; las cifras son estimaciones
          con un rango, calculadas sobre tus datos, y no recomiendan ninguna operación.
        </p>
      </div>
      {open && <NewsDetail item={open} onClose={closeDetail} />}
    </>
  );
}
