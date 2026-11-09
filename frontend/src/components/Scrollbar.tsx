/**
 * Barra de scroll propia para un contenedor con `overflow-y: auto` (el <main> en escritorio y la
 * conversación del asistente). La barra nativa del contenedor se oculta con `.kairos-scroll`
 * (index.css); esta se dibuja encima, pegada a su borde derecho.
 *
 * - Fina en reposo; al pasar el ratón (o al arrastrar) se ensancha y se oscurece, con transición.
 * - Cursor de mano. Se puede arrastrar el pulgar o pulsar en el carril para saltar a ese punto.
 * - Es decorativa para el lector de pantalla (aria-hidden): la rueda, el tacto y el teclado
 *   siguen desplazando el contenedor como siempre.
 * - Se oculta sola si el contenido cabe. La posición se escribe en el DOM, sin re-renderizar.
 */
import { useEffect, useRef, type PointerEvent, type RefObject } from "react";

const MIN_THUMB_PX = 32;
const INSET_PX = 4; // margen arriba y abajo del carril

interface ScrollbarProps {
  target: RefObject<HTMLElement | null>;
  className?: string;
}

export function Scrollbar({ target, className = "" }: ScrollbarProps) {
  const track = useRef<HTMLDivElement>(null);
  const thumb = useRef<HTMLDivElement>(null);
  const drag = useRef<{ y: number; top: number; ratio: number } | null>(null);

  useEffect(() => {
    const el = target.current;
    const bar = track.current;
    const knob = thumb.current;
    if (!el || !bar || !knob) return;

    const update = () => {
      const { scrollHeight, clientHeight, scrollTop } = el;
      const overflow = scrollHeight - clientHeight;
      const visible = overflow > 1;
      bar.style.opacity = visible ? "1" : "0";
      bar.style.pointerEvents = visible ? "auto" : "none";
      if (!visible) return;
      const trackH = bar.clientHeight;
      const thumbH = Math.max(MIN_THUMB_PX, (clientHeight / scrollHeight) * trackH);
      knob.style.height = `${thumbH}px`;
      knob.style.transform = `translateY(${(scrollTop / overflow) * (trackH - thumbH)}px)`;
    };

    update();
    el.addEventListener("scroll", update, { passive: true });
    const resize = typeof ResizeObserver === "function" ? new ResizeObserver(update) : null;
    const observeChildren = () => {
      if (!resize) return;
      resize.disconnect();
      resize.observe(el);
      for (const child of Array.from(el.children)) resize.observe(child);
    };
    observeChildren();
    // Al cambiar de pantalla o llegar mensajes cambian los hijos: se vuelven a observar.
    const mutations = typeof MutationObserver === "function" ? new MutationObserver(() => {
      observeChildren();
      update();
    }) : null;
    mutations?.observe(el, { childList: true });
    return () => {
      el.removeEventListener("scroll", update);
      resize?.disconnect();
      mutations?.disconnect();
    };
  }, [target]);

  const onThumbDown = (e: PointerEvent<HTMLDivElement>) => {
    const el = target.current;
    const bar = track.current;
    const knob = thumb.current;
    if (!el || !bar || !knob || e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.setPointerCapture(e.pointerId);
    const free = bar.clientHeight - knob.offsetHeight;
    drag.current = {
      y: e.clientY,
      top: el.scrollTop,
      ratio: free > 0 ? (el.scrollHeight - el.clientHeight) / free : 0,
    };
    bar.dataset.dragging = "";
  };
  const onThumbMove = (e: PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    const el = target.current;
    if (!d || !el) return;
    el.scrollTo({ top: d.top + (e.clientY - d.y) * d.ratio });
  };
  const onThumbUp = () => {
    drag.current = null;
    if (track.current) delete track.current.dataset.dragging;
  };

  // Pulsar en el carril: lleva el centro del pulgar a ese punto.
  const onTrackDown = (e: PointerEvent<HTMLDivElement>) => {
    const el = target.current;
    const bar = track.current;
    const knob = thumb.current;
    if (!el || !bar || !knob || e.button !== 0) return;
    const rect = bar.getBoundingClientRect();
    const free = rect.height - knob.offsetHeight;
    if (free <= 0) return;
    const pos = Math.min(Math.max(e.clientY - rect.top - knob.offsetHeight / 2, 0), free);
    el.scrollTo({ top: (pos / free) * (el.scrollHeight - el.clientHeight), behavior: "smooth" });
  };

  return (
    <div
      ref={track}
      aria-hidden="true"
      onPointerDown={onTrackDown}
      className={`kairos-scrollbar group absolute right-0.5 z-10 flex w-3.5 cursor-pointer justify-center opacity-0 transition-opacity duration-200 ${className}`}
      style={{ top: INSET_PX, bottom: INSET_PX }}
    >
      <div
        ref={thumb}
        onPointerDown={onThumbDown}
        onPointerMove={onThumbMove}
        onPointerUp={onThumbUp}
        onPointerCancel={onThumbUp}
        className="kairos-scrollbar-thumb absolute left-1/2 top-0 -translate-x-1/2 cursor-pointer touch-none rounded-full"
      />
    </div>
  );
}
