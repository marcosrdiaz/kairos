import type { ReactNode } from "react";
import type { NewsCategory } from "../../api/generated/schema";
import { NEWS_CATEGORY_ICON_PATH } from "../market/chart/markers/newsCategoryIconPaths";
import { CalendarIcon } from "../../components/icons";
import { formatDate } from "../../lib/format";
import { cn } from "../../lib/cn";
import { CATEGORY_LABEL } from "./labels";

const COVER_TONE: Record<NewsCategory, { background: string; foreground: string }> = {
  company: { background: "bg-icon-blue-bg", foreground: "text-icon-blue" },
  earnings: { background: "bg-icon-purple-bg", foreground: "text-icon-purple" },
  central_bank: { background: "bg-icon-gold-bg", foreground: "text-icon-gold" },
  politics: { background: "bg-icon-red-bg", foreground: "text-icon-red" },
  commodities: { background: "bg-icon-gold-bg", foreground: "text-icon-gold" },
  fx: { background: "bg-icon-green-bg", foreground: "text-icon-green" },
  other: { background: "bg-nodata-bg", foreground: "text-nodata" },
};

const CATEGORY_ART: Record<NewsCategory, ReactNode> = {
  company: (
    <>
      <rect x="28" y="34" width="31" height="51" rx="3" />
      <rect x="64" y="17" width="37" height="68" rx="3" />
      <rect x="106" y="42" width="27" height="43" rx="3" />
      <path d="M38 45h5m8 0h3M38 57h5m8 0h3M74 31h6m9 0h4M74 45h6m9 0h4M74 59h6m9 0h4M113 54h5m8 0M113 66h5m8 0M18 86h128" />
    </>
  ),
  earnings: (
    <>
      <path d="M48 15h43l22 22v49H48z" />
      <path d="M91 15v23h22M61 49h37M61 61h26M61 73h19" />
      <circle cx="128" cy="68" r="18" />
      <path d="m120 68 6 6 11-13" />
    </>
  ),
  central_bank: (
    <>
      <path d="m23 39 57-24 57 24H23ZM29 84h102M37 46v32m21-32v32m22-32v32m21-32v32m21-32v32" />
    </>
  ),
  politics: (
    <>
      <path d="M37 37h67a9 9 0 0 1 9 9v20a9 9 0 0 1-9 9H71L53 88v-13h-7a9 9 0 0 1-9-9V46a9 9 0 0 1 9-9Z" />
      <path d="M57 54h36m-36 12h24" />
      <path d="M119 28h20v18h-20zM129 46v18" />
    </>
  ),
  commodities: (
    <>
      <path d="M80 14C67 34 48 53 48 68a32 32 0 0 0 64 0c0-15-19-34-32-54Z" />
      <path d="M66 70a14 14 0 0 0 14 14" />
      <circle cx="126" cy="31" r="8" />
      <circle cx="35" cy="40" r="5" />
    </>
  ),
  fx: (
    <>
      <path d="M39 43a34 34 0 0 1 58-19l9 9m0 0V17m0 16H90M121 61a34 34 0 0 1-58 19l-9-9m0 0v16m0-16h16" />
      <path d="M60 52h18m-9-9v18m18-9h19" />
    </>
  ),
  other: (
    <>
      <circle cx="80" cy="51" r="25" />
      <circle cx="80" cy="51" r="42" />
      <circle cx="80" cy="51" r="8" />
      <path d="m114 23 5-10m-3 14 10-4M39 76l-7 9m12-5-3 11" />
    </>
  ),
};

function CategoryArtwork({ category }: { category: NewsCategory }) {
  return (
    <svg
      viewBox="0 0 160 100"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      data-news-art={category}
      className="h-full w-full"
    >
      {CATEGORY_ART[category]}
    </svg>
  );
}

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
 * Fila de metadatos de una noticia: chip de categoría y fecha (carrusel de Inicio, encima del
 * título). Lo mismo que lleva la portada completa, para que la portada compacta sea solo imagen.
 */
export function NewsMeta({ category, publishedAt }: { category: NewsCategory; publishedAt: string }) {
  const tone = COVER_TONE[category];
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <span
        className={cn(
          "inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-0.5 text-sm font-semibold",
          tone.foreground,
        )}
      >
        <CategoryIcon category={category} className="size-4" />
        {CATEGORY_LABEL[category]}
      </span>
      <time dateTime={publishedAt} className="inline-flex items-center gap-2 text-sm text-ink-muted">
        <CalendarIcon className={cn("size-4", tone.foreground)} />
        {formatDate(publishedAt)}
      </time>
    </div>
  );
}

/**
 * Portada editorial geométrica por categoría; no representa una noticia o cifra concreta.
 */
export function NewsCover({
  category,
  publishedAt,
  large = false,
  dense = false,
}: {
  category: NewsCategory;
  publishedAt: string;
  large?: boolean;
  /** Sin alto mínimo: la portada se adapta al hueco que le dan (carrusel de Inicio). */
  dense?: boolean;
}) {
  const tone = COVER_TONE[category];
  // Compacta (carrusel de Inicio): solo la ilustración, a todo el recuadro. La categoría y la fecha
  // las pinta `NewsMeta` junto al texto.
  if (dense) {
    return (
      <div
        aria-hidden="true"
        className={cn(
          "relative isolate flex size-full items-center justify-center overflow-hidden rounded-control",
          tone.background,
          tone.foreground,
        )}
      >
        <div className="flex size-full items-center justify-center p-4 opacity-75 [&>svg]:max-h-full [&>svg]:max-w-full">
          <CategoryArtwork category={category} />
        </div>
      </div>
    );
  }
  return (
    <div
      className={cn(
        "relative isolate flex items-center overflow-hidden text-ink",
        large
          ? "min-h-40 rounded-control px-5 py-5"
          : "min-h-28 rounded-t-[15px] px-4 py-4",
        tone.background,
      )}
    >
      <div className="relative z-10 flex min-w-0 flex-col items-start gap-3">
        <span
          className={cn(
            "inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-sm font-semibold",
            tone.foreground,
          )}
        >
          <CategoryIcon category={category} className="size-4" />
          {CATEGORY_LABEL[category]}
        </span>
        <time dateTime={publishedAt} className="inline-flex items-center gap-2 text-sm text-ink">
          <CalendarIcon className={cn("size-4", tone.foreground)} />
          {formatDate(publishedAt)}
        </time>
      </div>
      <div
        aria-hidden="true"
        className={cn(
          "pointer-events-none absolute inset-y-0 right-1 z-0 flex w-[46%] items-center justify-center opacity-75",
          tone.foreground,
        )}
      >
        <CategoryArtwork category={category} />
      </div>
    </div>
  );
}
