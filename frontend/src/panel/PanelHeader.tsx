import { useEffect, useId, useRef, useState } from "react";
import { usePortfolios } from "../app/portfolio-picker/usePortfolios";
import { ArrowLeftIcon, ArrowRightIcon } from "../components/icons";
import { PANEL_SECTIONS } from "./sections";

interface PanelHeaderProps {
  portfolioId: string;
}

type SectionId = (typeof PANEL_SECTIONS)[number]["id"];

/** Fracción de la altura visible que tiene que pasar el título de un bloque para darlo por leído. */
const READ_LINE = 0.3;
const SCROLL_BUTTON =
  "grid size-touch shrink-0 place-items-center rounded-full border border-line-strong bg-surface text-ink transition-colors hover:border-accent disabled:cursor-not-allowed disabled:opacity-40 motion-reduce:transition-none";

/**
 * Bloque que se está leyendo: el último cuyo comienzo ha pasado el 30 % superior de la pantalla;
 * si ya no se puede bajar más, el último bloque (si no, el final nunca se marcaría). Escucha el
 * desplazamiento de la ventana (móvil) y del <main> (escritorio, donde desplaza él).
 */
function useActiveSection(): SectionId | null {
  const [active, setActive] = useState<SectionId | null>(null);
  useEffect(() => {
    const main = document.getElementById("contenido");
    let frame = 0;
    const update = () => {
      frame = 0;
      const line = window.innerHeight * READ_LINE;
      const atBottom =
        (main !== null && main.scrollHeight > main.clientHeight
          ? main.scrollHeight - main.scrollTop - main.clientHeight
          : document.documentElement.scrollHeight - window.scrollY - window.innerHeight) < 2;
      let current: SectionId | null = null;
      for (const s of PANEL_SECTIONS) {
        const el = document.getElementById(s.id);
        if (el && el.getBoundingClientRect().top <= line) current = s.id;
      }
      const lastId = PANEL_SECTIONS[PANEL_SECTIONS.length - 1]?.id ?? null;
      setActive(atBottom && current !== null ? lastId : current);
    };
    const schedule = () => {
      if (frame === 0) frame = requestAnimationFrame(update);
    };
    const targets: (Window | HTMLElement)[] = main ? [window, main] : [window];
    for (const t of targets) t.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      if (frame !== 0) cancelAnimationFrame(frame);
      for (const t of targets) t.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  }, []);
  return active;
}

/**
 * Cabecera única del panel (T5-16): título con la cartera que se está viendo y, debajo, una barra
 * de chips fija al desplazarse que lleva a cada bloque y marca el que se está leyendo.
 * Un aviso `aria-live` dice qué cartera se está viendo al cambiarla desde Cartera.
 * En escritorio el <main> desplaza con 2,5 rem de relleno arriba: una sombra del color del fondo
 * tapa ese hueco para que no asome el contenido por encima de la barra fija.
 */
export function PanelHeader({ portfolioId }: PanelHeaderProps) {
  const { data } = usePortfolios();
  const name = data?.find((p) => p.id === portfolioId)?.name;
  const active = useActiveSection();
  const navId = useId();
  const listRef = useRef<HTMLUListElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  useEffect(() => {
    const list = listRef.current;
    if (!list) return;

    const syncScrollButtons = () => {
      const maxScroll = list.scrollWidth - list.clientWidth;
      setCanScrollLeft(list.scrollLeft > 1);
      setCanScrollRight(maxScroll > 1 && list.scrollLeft < maxScroll - 1);
    };

    syncScrollButtons();
    list.addEventListener("scroll", syncScrollButtons, { passive: true });
    window.addEventListener("resize", syncScrollButtons);
    const resizeObserver =
      typeof ResizeObserver === "undefined" ? null : new ResizeObserver(syncScrollButtons);
    resizeObserver?.observe(list);

    return () => {
      list.removeEventListener("scroll", syncScrollButtons);
      window.removeEventListener("resize", syncScrollButtons);
      resizeObserver?.disconnect();
    };
  }, []);

  const scrollSections = (direction: -1 | 1) => {
    const list = listRef.current;
    if (!list) return;
    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    list.scrollBy({
      left: direction * Math.max(180, Math.round(list.clientWidth * 0.72)),
      behavior: reducedMotion ? "auto" : "smooth",
    });
  };

  // En móvil la barra se desplaza en horizontal: lleva a la vista el chip del bloque activo.
  useEffect(() => {
    const list = listRef.current;
    const chip = active ? list?.querySelector<HTMLElement>(`a[href="#${active}"]`) : null;
    if (!list || !chip) return;
    const left = chip.offsetLeft - list.offsetLeft;
    if (left < list.scrollLeft || left + chip.offsetWidth > list.scrollLeft + list.clientWidth) {
      list.scrollLeft = left - 16;
    }
  }, [active]);

  return (
    <>
      {/* Por encima de la sombra color papel de la barra, que tapa el hueco superior del <main>. */}
      <div className="relative z-20 grid grid-cols-[minmax(0,1fr)_auto] items-start gap-x-4 gap-y-1">
        <div className="min-w-0">
          <h1 className="m-0 text-2xl font-semibold leading-tight text-ink">Panel de contexto</h1>
          <p className="m-0 mt-1 text-base text-ink-muted">
            Datos, eventos y exposiciones que ayudan a entender tu cartera.
          </p>
        </div>
        {name && (
          <p className="m-0 justify-self-end rounded-full bg-accent-tint px-3 py-1 text-sm font-medium text-ink">
            <span className="text-ink-muted">Cartera:</span> {name}
          </p>
        )}
      </div>
      <nav
        aria-label="Bloques del panel"
        className="sticky top-(--kairos-header-height) z-10 -mx-1 -mt-6 -mb-3 bg-paper px-1 py-3 lg:top-0 lg:shadow-[0_-2.5rem_0_0_var(--color-paper)]"
      >
        <div className="flex min-w-0 items-center gap-2">
          <button
            type="button"
            aria-label="Desplazar bloques a la izquierda"
            aria-controls={navId}
            disabled={!canScrollLeft}
            onClick={() => scrollSections(-1)}
            className={SCROLL_BUTTON}
          >
            <ArrowLeftIcon className="size-5" />
          </button>
          <ul
            id={navId}
            ref={listRef}
            className="panel-chip-rail m-0 flex min-w-0 flex-1 list-none gap-2 overflow-x-auto p-0"
          >
            {PANEL_SECTIONS.map((s) => (
              <li key={s.id} className="flex shrink-0">
                <a
                  href={`#${s.id}`}
                  aria-current={active === s.id ? "location" : undefined}
                  className="inline-flex min-h-touch items-center rounded-full border border-line bg-surface px-4 text-base font-medium text-ink-muted no-underline transition-colors hover:border-accent hover:text-ink aria-[current=location]:border-accent aria-[current=location]:bg-accent aria-[current=location]:text-on-accent motion-reduce:transition-none"
                >
                  {s.label}
                </a>
              </li>
            ))}
          </ul>
          <button
            type="button"
            aria-label="Desplazar bloques a la derecha"
            aria-controls={navId}
            disabled={!canScrollRight}
            onClick={() => scrollSections(1)}
            className={SCROLL_BUTTON}
          >
            <ArrowRightIcon className="size-5" />
          </button>
        </div>
      </nav>
      <p role="status" aria-live="polite" className="sr-only">
        {name ? `Mostrando la cartera de ${name}` : ""}
      </p>
    </>
  );
}
