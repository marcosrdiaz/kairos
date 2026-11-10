/*
 * Cambio suave de un texto por otro. Adaptado de `text-morph.tsx` de Componentry
 * (https://github.com/harshjdhv/componentry, MIT).
 * Cambios: sin rotación automática (solo anima cuando cambia `text`), sin filtro SVG de
 * umbral, con `prefers-reduced-motion` el cambio es instantáneo, y un único nodo con el texto
 * actual (el que lleva `aria-live`): la frase saliente es una copia con `aria-hidden` que sale
 * del DOM en cuanto acaba el fundido. La altura pasa de la antigua a la nueva sin saltar.
 */
import { animate, motion } from "motion/react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { cn } from "../lib/cn";

/** Duración del fundido y del cambio de altura, en segundos (200–300 ms, ease-out). */
const DURATION = 0.24;
/** La frase saliente se va más rápido de lo que entra la nueva (salida más corta que entrada). */
const EXIT_DURATION = 0.16;
/** ease-out fuerte (Emil Kowalski): el `easeOut` de serie arranca sin pegada. */
const EASE_OUT = [0.23, 1, 0.32, 1] as const;

function prefersReducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export interface TextMorphProps {
  text: string;
  className?: string;
}

export function TextMorph({ text, className }: TextMorphProps) {
  const [shownText, setShownText] = useState(text);
  const [outgoing, setOutgoing] = useState<string | null>(null);
  const wrapperRef = useRef<HTMLSpanElement>(null);
  const currentRef = useRef<HTMLSpanElement>(null);
  const lastHeight = useRef(0);
  const previousText = useRef(text);

  // Ajuste de estado durante el render: así la frase nueva y la saliente entran juntas, sin
  // un fotograma intermedio con la nueva sola.
  if (text !== shownText) {
    setShownText(text);
    setOutgoing(prefersReducedMotion() ? null : shownText);
  }

  useLayoutEffect(() => {
    const wrapper = wrapperRef.current;
    const current = currentRef.current;
    if (!wrapper || !current) return;
    const from = lastHeight.current;
    const to = current.offsetHeight;
    lastHeight.current = to;
    const changed = previousText.current !== text;
    previousText.current = text;
    if (!changed || prefersReducedMotion()) return;

    const fade = animate(
      current,
      { opacity: [0, 1], filter: ["blur(3px)", "blur(0px)"] },
      { duration: DURATION, ease: EASE_OUT },
    );
    const grow =
      from > 0 && to > 0 && from !== to
        ? animate(wrapper, { height: [from, to] }, { duration: DURATION, ease: EASE_OUT })
        : null;
    if (grow) wrapper.style.overflow = "hidden";
    void grow?.finished.then(() => {
      wrapper.style.height = "";
      wrapper.style.overflow = "";
    });
    return () => {
      // Si el texto cambia a mitad de camino, la siguiente animación parte de lo que se ve.
      if (grow) lastHeight.current = wrapper.getBoundingClientRect().height;
      fade.stop();
      grow?.stop();
      wrapper.style.height = "";
      wrapper.style.overflow = "";
    };
  }, [text]);

  useEffect(() => {
    if (outgoing === null) return;
    const timer = setTimeout(() => setOutgoing(null), DURATION * 1000 + 40);
    return () => clearTimeout(timer);
  }, [outgoing]);

  return (
    <span ref={wrapperRef} className={cn("relative block", className)}>
      {outgoing !== null && (
        <motion.span
          key={outgoing}
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 block select-none"
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          transition={{ duration: EXIT_DURATION, ease: EASE_OUT }}
        >
          {outgoing}
        </motion.span>
      )}
      <span ref={currentRef} aria-live="polite" aria-atomic="true" className="block">
        {shownText}
      </span>
    </span>
  );
}
