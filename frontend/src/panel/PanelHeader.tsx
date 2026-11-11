import { useEffect, useRef, useState } from "react";
import { usePortfolios } from "../app/portfolio-picker/usePortfolios";
import { PANEL_SECTIONS } from "./sections";

interface PanelHeaderProps {
  portfolioId: string;
}

type SectionId = (typeof PANEL_SECTIONS)[number]["id"];

/** Fracción de la altura visible que tiene que pasar el título de un bloque para darlo por leído. */
const READ_LINE = 0.3;

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
  const listRef = useRef<HTMLUListElement>(null);

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
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <h1 className="m-0 text-2xl font-semibold leading-tight text-ink">Panel de contexto</h1>
        {name && (
          <p className="m-0 rounded-full bg-accent-tint px-3 py-1 text-sm font-medium text-ink">
            <span className="text-ink-muted">Cartera</span> {name}
          </p>
        )}
      </div>
      <nav
        aria-label="Bloques del panel"
        className="sticky top-(--kairos-header-height) z-10 -mx-1 -mt-9 -mb-3 bg-paper px-1 py-3 lg:top-0 lg:shadow-[0_-2.5rem_0_0_var(--color-paper)]"
      >
        <ul
          ref={listRef}
          className="m-0 flex list-none gap-2 overflow-x-auto p-0 [scrollbar-width:none]"
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
      </nav>
      <p role="status" aria-live="polite" className="sr-only">
        {name ? `Mostrando la cartera de ${name}` : ""}
      </p>
    </>
  );
}
