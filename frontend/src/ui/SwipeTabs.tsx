/*
 * Pestañas con indicador que se desliza y panel que se cambia arrastrando. Adaptado de
 * «Swipe Tabs» (`smooth-tab.tsx`) de Kokonut UI (https://github.com/KokonutUI/kokonutui, MIT).
 * Cambios: el indicador usa `layoutId` de motion (sin medir a mano), el gesto se reduce a un
 * deslizamiento horizontal con umbral, se sigue el patrón ARIA de pestañas (flechas, Inicio y
 * Fin) y se quitan los iconos de lucide (DESIGN.md no admite librerías de iconos sin decisión).
 * Todos los paneles quedan montados y los inactivos se ocultan con `hidden`, para no perder un
 * formulario a medias al cambiar de pestaña (T5-05). Con `swipeable={false}` el panel no se
 * cambia arrastrando: solo con las pestañas.
 */
import { useId, useRef, useState, type KeyboardEvent, type PointerEvent, type ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";
import { cn } from "../lib/cn";

export interface SwipeTabItem {
  id: string;
  title: string;
  content: ReactNode;
}

export interface SwipeTabsProps {
  items: readonly SwipeTabItem[];
  /** Nombre accesible de la lista de pestañas. */
  label: string;
  className?: string;
  /** Cambiar de panel deslizándolo en horizontal (por defecto, sí). */
  swipeable?: boolean;
}

const SWIPE_PX = 48;

export function SwipeTabs({ items, label, className, swipeable = true }: SwipeTabsProps) {
  const baseId = useId();
  const reduceMotion = useReducedMotion();
  const [activeId, setActiveId] = useState(items[0]?.id ?? "");
  const tabs = useRef(new Map<string, HTMLButtonElement>());
  const start = useRef<{ x: number; y: number } | null>(null);
  const index = Math.max(0, items.findIndex((item) => item.id === activeId));
  const swipe = swipeable
    ? {
        onPointerDown: (event: PointerEvent<HTMLDivElement>) => (start.current = { x: event.clientX, y: event.clientY }),
        onPointerUp,
        onPointerCancel: () => (start.current = null),
      }
    : {};

  function select(next: number, focus = false) {
    const item = items[(next + items.length) % items.length];
    if (!item) return;
    setActiveId(item.id);
    if (focus) tabs.current.get(item.id)?.focus();
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const target = { ArrowRight: index + 1, ArrowLeft: index - 1, Home: 0, End: items.length - 1 }[event.key];
    if (target === undefined) return;
    event.preventDefault();
    select(target, true);
  }

  function onPointerUp(event: PointerEvent<HTMLDivElement>) {
    const origin = start.current;
    start.current = null;
    if (!origin) return;
    const dx = event.clientX - origin.x;
    const dy = event.clientY - origin.y;
    if (Math.abs(dx) < SWIPE_PX || Math.abs(dx) < Math.abs(dy) * 1.5) return;
    const next = index + (dx < 0 ? 1 : -1);
    if (next >= 0 && next < items.length) select(next);
  }

  return (
    <div className={className}>
      <div
        role="tablist"
        aria-label={label}
        onKeyDown={onKeyDown}
        className="grid w-full grid-flow-col auto-cols-fr gap-1 rounded-full border border-line bg-surface-muted p-1 @3xl/app-content:inline-flex @3xl/app-content:w-fit"
      >
        {items.map((item) => {
          const selected = item.id === items[index]?.id;
          return (
            <button
              key={item.id}
              ref={(node) => {
                if (node) tabs.current.set(item.id, node);
                else tabs.current.delete(item.id);
              }}
              id={`${baseId}-tab-${item.id}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`${baseId}-panel-${item.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => setActiveId(item.id)}
              className={cn(
                "relative min-h-touch min-w-0 rounded-full px-2 py-2 text-center text-base leading-tight font-medium whitespace-normal transition-colors @3xl/app-content:shrink-0 @3xl/app-content:px-5 @3xl/app-content:py-0 @3xl/app-content:whitespace-nowrap",
                selected ? "text-on-accent" : "text-ink-muted hover:text-ink",
              )}
            >
              {selected && (
                <motion.span
                  layoutId={`${baseId}-indicator`}
                  aria-hidden="true"
                  transition={reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 420, damping: 36 }}
                  className="absolute inset-0 rounded-full bg-accent"
                />
              )}
              <span className="relative">{item.title}</span>
            </button>
          );
        })}
      </div>
      {items.map((item, i) => (
        <div
          key={item.id}
          role="tabpanel"
          id={`${baseId}-panel-${item.id}`}
          aria-labelledby={`${baseId}-tab-${item.id}`}
          hidden={i !== index}
          tabIndex={0}
          {...swipe}
          className={cn("mt-4 rounded-card", swipeable && "touch-pan-y")}
        >
          {item.content}
        </div>
      ))}
    </div>
  );
}
