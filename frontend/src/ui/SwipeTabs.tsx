/*
 * Pestañas con indicador que se desliza y panel que se cambia arrastrando. Adaptado de
 * «Swipe Tabs» (`smooth-tab.tsx`) de Kokonut UI (https://github.com/KokonutUI/kokonutui, MIT).
 * Cambios: el indicador usa `layoutId` de motion (sin medir a mano), el gesto se reduce a un
 * deslizamiento horizontal con umbral, se sigue el patrón ARIA de pestañas (flechas, Inicio y
 * Fin) y se quitan los iconos de lucide (DESIGN.md no admite librerías de iconos sin decisión).
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
}

const SWIPE_PX = 48;

export function SwipeTabs({ items, label, className }: SwipeTabsProps) {
  const baseId = useId();
  const reduceMotion = useReducedMotion();
  const [activeId, setActiveId] = useState(items[0]?.id ?? "");
  const tabs = useRef(new Map<string, HTMLButtonElement>());
  const start = useRef<{ x: number; y: number } | null>(null);
  const index = Math.max(0, items.findIndex((item) => item.id === activeId));
  const active = items[index];

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
        className="inline-flex max-w-full gap-1 overflow-x-auto rounded-full border border-line bg-surface-muted p-1"
      >
        {items.map((item) => {
          const selected = item.id === activeId;
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
                "relative min-h-touch shrink-0 rounded-full px-5 text-base font-medium whitespace-nowrap transition-colors",
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
      {active && (
        <div
          role="tabpanel"
          id={`${baseId}-panel-${active.id}`}
          aria-labelledby={`${baseId}-tab-${active.id}`}
          tabIndex={0}
          onPointerDown={(event) => (start.current = { x: event.clientX, y: event.clientY })}
          onPointerUp={onPointerUp}
          onPointerCancel={() => (start.current = null)}
          className="mt-4 touch-pan-y rounded-card"
        >
          {active.content}
        </div>
      )}
    </div>
  );
}
