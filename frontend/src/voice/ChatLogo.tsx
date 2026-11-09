import { useId } from "react";

/**
 * Variante del logo para el asistente: la marca (dos barras y la K) dentro de un bocadillo de
 * chat, con una insignia de ondas de voz en la esquina (texto y voz). Mismos tokens que
 * `LogoMark`, así que cambia con el modo claro/oscuro. Decorativa: el nombre lo da el botón.
 */
interface ChatLogoProps {
  className?: string;
  /**
   * Bocadillo blanco con borde dorado: para ponerlo sobre un fondo de color (el botón
   * flotante), donde el bocadillo tiene que distinguirse del fondo y del borde del botón.
   */
  outlined?: boolean;
}

export function ChatLogo({ className = "size-12", outlined = false }: ChatLogoProps) {
  const id = `kairos-chat-${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true" focusable="false" className={className}>
      <defs>
        <linearGradient id={`${id}-mark`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="var(--kairos-color-gold)" />
          <stop offset="1" stopColor="var(--kairos-color-gold-deep)" />
        </linearGradient>
        <linearGradient id={`${id}-badge`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="var(--kairos-color-gold)" />
          <stop offset="1" stopColor="var(--kairos-color-gold-deep)" />
        </linearGradient>
      </defs>

      {/* Bocadillo: el cuadrado redondeado del logo con una cola abajo a la izquierda. */}
      <path
        d="M15 5h34a11 11 0 0 1 11 11v25a11 11 0 0 1-11 11H25l-11.5 8.5V51.6A11 11 0 0 1 4 41V16A11 11 0 0 1 15 5z"
        fill={outlined ? "var(--kairos-color-surface)" : "var(--kairos-color-bg)"}
        stroke={outlined ? "var(--kairos-color-gold-deep)" : "var(--kairos-color-border)"}
        strokeWidth={outlined ? 2.25 : 1.5}
        strokeLinejoin="round"
      />

      {/* La marca de LogoMark (viewBox 64×48), reducida y centrada en el bocadillo. */}
      <g transform="translate(13.5 15.5) scale(0.56)" fill={`url(#${id}-mark)`}>
        <rect x="1" y="29" width="8" height="17" rx="1.5" />
        <rect x="12" y="20" width="8" height="26" rx="1.5" />
        <rect x="23" y="4" width="9" height="42" rx="1.5" />
        <path d="M32 27 50.5 4H62L37.5 32.5z" />
        <path d="M37 25.5 43.5 19 63 46H51.5z" />
      </g>

      {/* Insignia de voz: círculo dorado con tres barras de onda. */}
      <circle cx="53" cy="11" r="9.5" fill={`url(#${id}-badge)`} stroke="var(--kairos-color-bg)" strokeWidth="2.5" />
      <g stroke="var(--kairos-color-bg)" strokeWidth="2" strokeLinecap="round">
        <path d="M49 10v2M53 7v8M57 9.5v3" />
      </g>
    </svg>
  );
}
