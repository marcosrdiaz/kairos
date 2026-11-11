import { useId, type ReactNode } from "react";

interface TraceHintProps {
  /** `calc_id` de la cifra (queda en el DOM para la trazabilidad). */
  calcId: string;
  /** Explicación breve de la cifra, en lenguaje llano. */
  text: string;
  /** Fuentes y fecha de los datos, en una línea. */
  source: string;
  children: ReactNode;
}

/**
 * «¿De dónde sale?» resumido y solo informativo: al pasar el ratón o con el foco aparece una
 * pista de dos líneas sobre la cifra (qué es y de qué datos sale). Sin modal ni clic. El texto
 * va enlazado con `aria-describedby`, así que el lector de pantalla lo lee al llegar a la cifra.
 */
export function TraceHint({ calcId, text, source, children }: TraceHintProps) {
  const id = useId();
  return (
    <span className="kchart-hint" tabIndex={0} aria-describedby={id} data-calc-id={calcId}>
      {children}
      <span id={id} role="tooltip" className="kchart-hint-pop">
        <span className="block">{text}</span>
        <span className="mt-1 block text-sm text-ink-muted">{source}</span>
      </span>
    </span>
  );
}
