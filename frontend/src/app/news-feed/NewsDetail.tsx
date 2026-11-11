import { useEffect, useId, useRef, type KeyboardEvent } from "react";
import { createPortal } from "react-dom";
import type { NewsItemOut } from "../../api/generated/schema";
import { CloseIcon } from "../../voice/icons";
import { NewsArticle } from "./NewsArticle";

/** `id` del <main> de AppShell. */
const MAIN_ID = "contenido";

/**
 * Detalle de una noticia sobre el contenido principal (T5-17). No es un `<dialog>` modal: ese
 * taparía toda la app. Va en el contenedor del `<main>` de AppShell, así el fondo oscurecido
 * solo cubre el contenido: la barra de navegación y el asistente abierto siguen a la vista y
 * usables. Mientras está abierto, el `<main>` queda `inert` (no se llega a él con el teclado
 * ni el lector); Escape, la cruz o el fondo lo cierran y el foco vuelve a la card.
 *
 * Fuera de AppShell (tests), se pinta en `document.body`.
 */
export function NewsDetail({ item, onClose }: { item: NewsItemOut; onClose: () => void }) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const host = document.getElementById(MAIN_ID)?.parentElement ?? document.body;

  useEffect(() => {
    closeRef.current?.focus();
    const content = document.getElementById(MAIN_ID);
    if (!content) return;
    const wasInert = content.inert;
    content.inert = true;
    return () => {
      content.inert = wasInert;
    };
  }, []);

  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      onClose();
    }
  };

  return createPortal(
    <div
      className="fixed inset-x-0 top-(--kairos-header-height) bottom-(--kairos-bottom-nav-height) z-10 lg:absolute lg:inset-0"
      onKeyDown={onKeyDown}
    >
      <div
        aria-hidden="true"
        onClick={onClose}
        className="news-detail-backdrop absolute inset-0"
      />
      <div
        role="dialog"
        aria-labelledby={titleId}
        className="news-detail-panel absolute inset-x-0 bottom-0 top-4 flex flex-col overflow-hidden rounded-t-card border border-line bg-surface lg:inset-y-6 lg:mx-auto lg:w-[min(46rem,calc(100%-3rem))] lg:rounded-card"
      >
        <div className="flex justify-end border-b border-line px-4 py-2">
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="Cerrar noticia"
            className="grid size-11 shrink-0 cursor-pointer place-items-center rounded-full text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink focus-visible:outline-focus"
          >
            <CloseIcon className="size-5" />
          </button>
        </div>
        <div className="kairos-scroll overflow-y-auto px-5 py-6 lg:px-8">
          <NewsArticle item={item} titleId={titleId} />
        </div>
      </div>
    </div>,
    host,
  );
}
