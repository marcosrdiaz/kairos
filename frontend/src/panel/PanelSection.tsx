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

/**
 * Bloque del panel: encabezado de nivel 2 enlazable y su contenido. El margen de desplazamiento
 * deja sitio a la barra de bloques fija (y en móvil, también a la cabecera de la app).
 */
export function PanelSection({ id, title, intro, step = 0, children }: PanelSectionProps) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-title`}
      style={{ "--panel-step": step } as CSSProperties}
      className={`panel-reveal scroll-mt-[calc(var(--kairos-header-height)+5rem)] lg:scroll-mt-24 ${
        step > 0 ? "border-t border-line pt-8" : ""
      }`}
    >
      <h2 id={`${id}-title`} className="m-0 text-2xl font-semibold leading-tight text-ink">
        {title}
      </h2>
      {intro && <p className="m-0 mt-1 text-base text-ink-muted">{intro}</p>}
      <div className="mt-5">{children}</div>
    </section>
  );
}
