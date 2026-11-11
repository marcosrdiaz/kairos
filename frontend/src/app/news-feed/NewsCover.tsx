import type { NewsCategory } from "../../api/generated/schema";
import { NEWS_CATEGORY_ICON_PATH } from "../market/chart/markers/newsCategoryIconPaths";
import { formatDate } from "../../lib/format";
import { cn } from "../../lib/cn";
import { CATEGORY_LABEL } from "./labels";

/** Icono de la categoría (trazo de 12 × 12, el mismo de los puntos de la gráfica de Inicio). */
export function CategoryIcon({
  category,
  className,
}: {
  category: NewsCategory;
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 12 12"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.1}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("shrink-0", className)}
    >
      <path d={NEWS_CATEGORY_ICON_PATH[category]} />
    </svg>
  );
}

/**
 * Portada de una noticia (T5-17). El contrato no trae imagen, así que no se inventa ninguna: un
 * tinte con el icono de la categoría, la categoría y la fecha. `large` en el detalle.
 */
export function NewsCover({
  category,
  publishedAt,
  large = false,
}: {
  category: NewsCategory;
  publishedAt: string;
  large?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-control bg-accent-tint text-ink",
        large ? "px-5 py-6" : "px-4 py-3",
      )}
    >
      <span
        className={cn(
          "flex items-center justify-center rounded-full bg-surface text-accent",
          large ? "size-14" : "size-10",
        )}
      >
        <CategoryIcon category={category} className={large ? "size-7" : "size-5"} />
      </span>
      <p className="m-0 flex flex-col text-sm leading-tight">
        <span className="font-semibold text-accent">{CATEGORY_LABEL[category]}</span>
        <time dateTime={publishedAt} className="text-ink-muted">
          {formatDate(publishedAt)}
        </time>
      </p>
    </div>
  );
}
