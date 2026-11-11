import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { TraceCardBody } from "./TraceCard";
import { contentBounds, overlaps, placeCard } from "./traceCardGeometry";
import { useTrace } from "./traceContext";
import "./trace.css";

/** Espera antes de abrir al pasar el ratón: cruzar una tabla no abre una tarjeta por cifra. */
const OPEN_MS = 250;
/** Margen para llevar el ratón de la cifra a la tarjeta sin que se cierre. */
const CLOSE_MS = 150;
const CARD_WIDTH_PX = 320;

type CardState = "closed" | "peek" | "pinned";

interface TraceAnchorProps {
  calcId: string;
  /** Cifra que encabeza la tarjeta; sin ella (`TraceLink`), la tarjeta empieza por la explicación. */
  value?: ReactNode;
  triggerClassName: string;
  /** Contenido del botón (la cifra o el texto del enlace). */
  children: ReactNode;
}

/** Sin la API de popover (navegadores antiguos, jsdom) la tarjeta queda `fixed` en su sitio del DOM. */
const POPOVER = typeof HTMLElement !== "undefined" && typeof HTMLElement.prototype.showPopover === "function";

/**
 * Cifra explicada al pasar o enfocar (T5-18): el ratón (tras una pausa) o el foco abren una tarjeta
 * anclada a la cifra; el clic o el toque la fijan y un segundo clic, Esc o pulsar fuera la cierran.
 * La tarjeta va en la capa superior (`popover`) para no quedar recortada por tablas con
 * desplazamiento, pero se coloca dentro del área de contenido: no tapa la barra lateral, la
 * cabecera, la barra inferior ni el chat. Desde ella, «Ver el cálculo completo» abre la hoja.
 */
export function TraceAnchor({ calcId, value, triggerClassName, children }: TraceAnchorProps) {
  const trace = useTrace();
  const baseId = useId();
  const cardId = `${baseId}-card`;
  const summaryId = `${baseId}-summary`;
  const [state, setState] = useState<CardState>("closed");
  const wrapper = useRef<HTMLSpanElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const card = useRef<HTMLSpanElement>(null);
  const timer = useRef<number | undefined>(undefined);
  /** El foco que se devuelve a la cifra al abrir la hoja no debe volver a abrir la tarjeta. */
  const quietFocus = useRef(false);
  const open = state !== "closed";

  const clearTimer = () => window.clearTimeout(timer.current);
  const after = (ms: number, fn: () => void) => {
    clearTimer();
    timer.current = window.setTimeout(fn, ms);
  };
  const close = () => {
    clearTimer();
    setState("closed");
  };
  const peekSoon = () => after(OPEN_MS, () => setState((s) => (s === "closed" ? "peek" : s)));
  const closeSoon = () => after(CLOSE_MS, () => setState((s) => (s === "peek" ? "closed" : s)));

  useEffect(() => clearTimer, []);

  // Capa superior y posición: al abrir, al desplazar, al cambiar el tamaño y al cargar la traza.
  useLayoutEffect(() => {
    const el = card.current;
    const anchor = trigger.current;
    if (!open || !el || !anchor) return;
    if (POPOVER && !el.matches(":popover-open")) el.showPopover();
    const place = () => {
      const bounds = contentBounds();
      const rect = anchor.getBoundingClientRect();
      if (rect.width > 0 && !overlaps(rect, bounds)) return setState("closed");
      const spot = placeCard(rect, { width: CARD_WIDTH_PX, height: el.scrollHeight + 2 }, bounds);
      el.style.left = `${spot.left}px`;
      el.style.top = `${spot.top}px`;
      el.style.width = `${spot.width}px`;
      el.style.maxHeight = `${spot.maxHeight}px`;
    };
    const onScroll = (event: Event) => {
      if (event.target instanceof Node && el.contains(event.target)) return; // la propia tarjeta
      if (state === "peek") setState("closed");
      else place();
    };
    place();
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", place);
    const observer = typeof ResizeObserver === "function" ? new ResizeObserver(place) : null;
    observer?.observe(el);
    return () => {
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", place);
      observer?.disconnect();
    };
  }, [open, state]);

  // Esc cierra; pulsar fuera de la cifra y de la tarjeta, también.
  useEffect(() => {
    if (!open) return;
    const close = () => {
      window.clearTimeout(timer.current);
      setState("closed");
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      const inside = wrapper.current?.contains(document.activeElement) ?? false;
      close();
      if (inside) trigger.current?.focus({ preventScroll: true });
    };
    const onPointerDown = (event: PointerEvent) => {
      if (event.target instanceof Node && wrapper.current?.contains(event.target)) return;
      close();
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointerDown);
    };
  }, [open]);

  if (!trace) return null;

  const showFull = () => {
    close();
    quietFocus.current = true;
    trigger.current?.focus({ preventScroll: true }); // la hoja devuelve el foco aquí al cerrarse
    quietFocus.current = false;
    trace.open(calcId);
  };

  return (
    <span
      ref={wrapper}
      className="relative inline"
      onBlur={(event) => {
        if (!(event.relatedTarget instanceof Node && wrapper.current?.contains(event.relatedTarget))) close();
      }}
    >
      <button
        ref={trigger}
        type="button"
        data-calc-id={calcId}
        aria-expanded={open}
        aria-controls={open ? cardId : undefined}
        aria-describedby={open ? summaryId : undefined}
        onPointerEnter={(event) => event.pointerType !== "touch" && peekSoon()}
        onPointerLeave={(event) => event.pointerType !== "touch" && closeSoon()}
        onFocus={() => !quietFocus.current && setState((s) => (s === "closed" ? "peek" : s))}
        onClick={() => {
          clearTimer();
          setState((s) => (s === "pinned" ? "closed" : "pinned"));
        }}
        className={triggerClassName}
      >
        {children}
      </button>
      {open && (
        <span
          ref={card}
          id={cardId}
          popover={POPOVER ? "manual" : undefined}
          role="group"
          aria-label="De dónde sale esta cifra"
          onPointerEnter={clearTimer}
          onPointerLeave={(event) => event.pointerType !== "touch" && state === "peek" && closeSoon()}
          className="trace-card fixed m-0 flex flex-col gap-1 overflow-y-auto px-4 py-3 text-left text-base font-normal not-italic text-ink [inset:auto]"
        >
          <TraceCardBody calcId={calcId} value={value} summaryId={summaryId} onFull={showFull} />
        </span>
      )}
    </span>
  );
}
