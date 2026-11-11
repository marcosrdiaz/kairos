import { useId } from "react";
import type { NewsItemOut } from "../../api/generated/schema";
import { NewsCover } from "./NewsCover";
import { NewsEffect } from "./NewsEffect";

/**
 * Card de la lista de Noticias (T5-17): portada, titular y «Cómo afecta a tu dinero». El titular
 * es el botón que abre el detalle y su `::after` cubre la card entera, así toda la card se puede
 * pulsar sin anidar botones; la cifra trazada queda por encima y sigue abriendo su traza.
 */
export function NewsCard({
  item,
  onOpen,
}: {
  item: NewsItemOut;
  onOpen: (id: string, opener: HTMLButtonElement) => void;
}) {
  const titleId = useId();
  return (
    <article
      aria-labelledby={titleId}
      className="group relative flex flex-col gap-4 rounded-card border border-line bg-surface p-4 transition-colors hover:border-accent focus-within:border-accent motion-reduce:transition-none"
    >
      <NewsCover category={item.category} publishedAt={item.published_at} />
      <h3 id={titleId} className="m-0 text-lg font-semibold leading-snug text-ink">
        <button
          type="button"
          aria-haspopup="dialog"
          onClick={(e) => onOpen(item.id, e.currentTarget)}
          className="cursor-pointer border-0 bg-transparent p-0 text-left [font:inherit] text-inherit outline-none after:absolute after:inset-0 after:rounded-card after:content-[''] focus-visible:after:outline-2 focus-visible:after:outline-offset-2 focus-visible:after:outline-focus group-hover:underline group-hover:decoration-line-strong group-hover:underline-offset-4"
        >
          {item.title}
        </button>
      </h3>
      <div className="mt-auto flex flex-col gap-2 border-t border-line pt-3">
        <h4 className="m-0 text-sm font-semibold text-ink-muted">Cómo afecta a tu dinero</h4>
        {/* Por encima del botón que cubre la card solo la cifra: abre su traza, no el detalle. */}
        <div className="pointer-events-none relative z-10 [&_button]:pointer-events-auto">
          <NewsEffect estimate={item.estimate} compact />
        </div>
      </div>
    </article>
  );
}
