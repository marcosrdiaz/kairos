import type { ReactNode } from "react";
import type { EventType } from "./labels";

/**
 * "Imagen" de cada noticia: ilustración por tipo de evento (los eventos no traen fotos).
 * Decorativa (aria-hidden): el tipo y el titular ya van en texto. Colores de los tokens,
 * así que cambia con el modo claro/oscuro.
 */
const TONE: Record<EventType, string> = {
  central_bank: "bg-icon-blue-bg text-icon-blue",
  commodity: "bg-icon-gold-bg text-icon-gold",
  earnings: "bg-icon-purple-bg text-icon-purple",
  fx: "bg-icon-green-bg text-icon-green",
  macro: "bg-accent-tint text-accent",
};

function Frame({ children }: { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 240 180"
      aria-hidden="true"
      focusable="false"
      className="h-full w-full"
      fill="none"
      stroke="currentColor"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="120" cy="90" r="70" fill="currentColor" opacity="0.08" stroke="none" />
      {children}
    </svg>
  );
}

const ART: Record<EventType, ReactNode> = {
  // Banco central: fachada con columnas y símbolo del euro.
  central_bank: (
    <Frame>
      <path d="M70 70l50-28 50 28z" />
      <path d="M66 70h108M70 130h100M64 140h112" />
      <path d="M82 78v46M104 78v46M136 78v46M158 78v46" />
      <path d="M128 52a10 10 0 1 0 0 12M108 56h16M108 61h16" strokeWidth="2.4" />
    </Frame>
  ),
  // Materias primas: gota de petróleo y barril.
  commodity: (
    <Frame>
      <path
        d="M92 52c-12 18-20 30-20 42a20 20 0 0 0 40 0c0-12-8-24-20-42z"
        fill="currentColor"
        fillOpacity="0.25"
      />
      <rect x="128" y="70" width="44" height="64" rx="8" />
      <path d="M128 90h44M128 114h44" />
    </Frame>
  ),
  // Resultados: informe con barras y lupa.
  earnings: (
    <Frame>
      <rect x="70" y="44" width="76" height="96" rx="8" />
      <path d="M86 120v-16M104 120v-30M122 120v-22" strokeWidth="6" />
      <circle cx="152" cy="118" r="18" fill="currentColor" fillOpacity="0.15" />
      <path d="M165 131l14 14" strokeWidth="5" />
    </Frame>
  ),
  // Divisas: dos monedas con flechas de cambio.
  fx: (
    <Frame>
      <circle cx="92" cy="80" r="24" fill="currentColor" fillOpacity="0.15" />
      <circle cx="148" cy="104" r="24" fill="currentColor" fillOpacity="0.15" />
      <path d="M96 70a10 10 0 1 0 0 20M84 76h12M84 82h12" strokeWidth="2.4" />
      <path d="M148 94v20M142 98c0-4 12-4 12 1s-12 3-12 8 12 4 12 0" strokeWidth="2.4" />
      <path d="M118 56c16 0 28 8 30 22l6-6M122 128c-16 0-28-8-30-22l-6 6" />
    </Frame>
  ),
  // Macroeconomía: globo terráqueo.
  macro: (
    <Frame>
      <circle cx="120" cy="90" r="48" />
      <ellipse cx="120" cy="90" rx="20" ry="48" />
      <path d="M72 90h96M80 66h80M80 114h80" />
    </Frame>
  ),
};

export function EventArt({ type }: { type: EventType }) {
  return (
    <div
      className={`flex h-full w-full items-center justify-center rounded-control p-4 ${TONE[type]}`}
    >
      {ART[type]}
    </div>
  );
}
