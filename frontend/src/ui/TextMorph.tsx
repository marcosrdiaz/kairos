/*
 * Cambio suave de un texto por otro (fundido con un desenfoque ligero). Adaptado de
 * `text-morph.tsx` de Componentry (https://github.com/harshjdhv/componentry, MIT).
 * Cambios: sin rotación automática (solo anima cuando cambia `text`), sin filtro SVG de
 * umbral, y con `prefers-reduced-motion` el cambio es instantáneo.
 */
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { cn } from "../lib/cn";

export interface TextMorphProps {
  text: string;
  className?: string;
}

export function TextMorph({ text, className }: TextMorphProps) {
  const reduceMotion = useReducedMotion();
  const hidden = { opacity: 0, filter: reduceMotion ? "blur(0px)" : "blur(4px)" };
  return (
    <span className={cn("inline-grid", className)}>
      <span className="sr-only" aria-live="polite">
        {text}
      </span>
      <AnimatePresence initial={false}>
        <motion.span
          key={text}
          aria-hidden="true"
          style={{ gridArea: "1 / 1" }}
          initial={hidden}
          animate={{ opacity: 1, filter: "blur(0px)" }}
          exit={hidden}
          transition={{ duration: reduceMotion ? 0 : 0.32, ease: "easeOut" }}
        >
          {text}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}
