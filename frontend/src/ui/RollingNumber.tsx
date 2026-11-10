/*
 * Número que rueda hasta su nuevo valor. Adaptado de `rolling-number.tsx` de Cult UI
 * (https://github.com/nolly-studio/cult-ui, MIT). Cambios: muelle sobreamortiguado (sin
 * rebote: «calma, nunca alarma»), salto directo con `prefers-reduced-motion`, y el valor
 * final siempre disponible para lectores de pantalla.
 * No calcula nada: `value` y `format` vienen de fuera (en la app, de `lib/format.ts` y con `Traced`).
 */
import { useEffect } from "react";
import { motion, useReducedMotion, useSpring, useTransform } from "motion/react";
import { cn } from "../lib/cn";

export interface RollingNumberProps {
  value: number;
  format: (value: number) => string;
  className?: string;
}

export function RollingNumber({ value, format, className }: RollingNumberProps) {
  const reduceMotion = useReducedMotion();
  const spring = useSpring(value, { stiffness: 120, damping: 26, mass: 0.8 });
  const display = useTransform(spring, (current) => format(current));

  useEffect(() => {
    if (reduceMotion) spring.jump(value);
    else spring.set(value);
  }, [spring, value, reduceMotion]);

  return (
    <span className={cn("tabular-nums", className)}>
      <motion.span aria-hidden="true">{display}</motion.span>
      <span className="sr-only">{format(value)}</span>
    </span>
  );
}
