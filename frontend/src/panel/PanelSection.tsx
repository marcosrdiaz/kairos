import type { CSSProperties, ReactNode } from "react";

interface PanelSectionProps {
  id: string;
  title: string;
  /** Una línea que dice qué hay en el bloque. */
  intro?: string;
  /** Orden de entrada (0, 1, 2…): escalona la aparición 45 ms por bloque. */
  step?: number;
  children: ReactNode;
}

/** Bloque del panel: encabezado de nivel 2 enlazable y su contenido. */
export function PanelSection({ id, title, intro, step = 0, children }: PanelSectionProps) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-title`}
      style={{ "--panel-step": step } as CSSProperties}
      className="panel-reveal scroll-mt-24"
    >
      <h2 id={`${id}-title`} className="m-0 text-2xl font-semibold leading-tight text-ink">
        {title}
      </h2>
      {intro && <p className="m-0 mt-1 max-w-[65ch] text-base text-ink-muted">{intro}</p>}
      <div className="mt-5">{children}</div>
    </section>
  );
}
