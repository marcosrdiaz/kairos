/*
 * Tarjeta con un foco de luz suave que sigue al ratón. Implementación propia (un degradado
 * radial cuya posición se guarda en dos variables CSS), por la idea de «Spotlight Card» de
 * React Bits. NO se copia código de React Bits: su licencia es MIT + Commons Clause y no se
 * considera equivalente a MIT (ver la decisión de dependencias del laboratorio).
 * Solo con ratón: en táctil y con `prefers-reduced-motion` no se muestra.
 */
import { useRef, type PointerEvent, type ReactNode } from "react";
import { cn } from "../lib/cn";

export interface SpotlightCardProps {
  children: ReactNode;
  className?: string;
}

const SPOT =
  "radial-gradient(220px circle at var(--spot-x, 50%) var(--spot-y, 50%), " +
  "color-mix(in srgb, var(--kairos-color-gold) 22%, transparent), transparent 70%)";

export function SpotlightCard({ children, className }: SpotlightCardProps) {
  const ref = useRef<HTMLDivElement>(null);

  function move(event: PointerEvent<HTMLDivElement>) {
    const element = ref.current;
    if (!element || event.pointerType !== "mouse") return;
    const rect = element.getBoundingClientRect();
    element.style.setProperty("--spot-x", `${event.clientX - rect.left}px`);
    element.style.setProperty("--spot-y", `${event.clientY - rect.top}px`);
  }

  return (
    <div
      ref={ref}
      onPointerMove={move}
      className={cn("group relative overflow-hidden rounded-card border border-line bg-surface p-5", className)}
    >
      <div
        aria-hidden="true"
        style={{ background: SPOT }}
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100 motion-reduce:hidden"
      />
      <div className="relative">{children}</div>
    </div>
  );
}
