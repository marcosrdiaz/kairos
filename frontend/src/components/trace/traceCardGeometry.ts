/** Rectángulo en coordenadas de la ventana (como `getBoundingClientRect`). */
export interface Box {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

export interface CardPlacement {
  left: number;
  top: number;
  width: number;
  /** Alto disponible en el lado elegido; si el contenido no cabe, la tarjeta se desplaza por dentro. */
  maxHeight: number;
  side: "below" | "above";
}

const GAP_PX = 8;

/**
 * Dónde se abre la tarjeta de una cifra: debajo y alineada a su izquierda; arriba si debajo no
 * cabe y arriba hay más sitio. Nunca sale de `bounds` (el área de contenido: sin barra lateral,
 * cabecera, barra inferior ni chat). Solo geometría: no mide ni toca el DOM.
 */
export function placeCard(anchor: Box, size: { width: number; height: number }, bounds: Box): CardPlacement {
  const width = Math.max(0, Math.min(size.width, bounds.right - bounds.left));
  const left = Math.max(bounds.left, Math.min(anchor.left, bounds.right - width));
  const below = Math.max(0, bounds.bottom - anchor.bottom - GAP_PX);
  const above = Math.max(0, anchor.top - bounds.top - GAP_PX);
  const side = size.height <= below || below >= above ? "below" : "above";
  const maxHeight = side === "below" ? below : above;
  const height = Math.min(size.height, maxHeight);
  const top = side === "below" ? anchor.bottom + GAP_PX : anchor.top - GAP_PX - height;
  return { left, top, width, maxHeight, side };
}

/** ¿Se ve algo de la cifra dentro del área de contenido? */
export function overlaps(a: Box, b: Box): boolean {
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}

/**
 * Área de contenido visible, leída del DOM de `AppShell`: el ancho de `<main id="contenido">` (deja
 * fuera la barra lateral y el chat de escritorio) y, en móvil, el alto entre la cabecera fija y la
 * barra de navegación inferior. Sin `AppShell` (tests, `/lab`), la ventana entera.
 */
export function contentBounds(): Box {
  const bounds: Box = { left: 0, top: 0, right: window.innerWidth, bottom: window.innerHeight };
  const main = document.getElementById("contenido");
  if (!main) return bounds;
  const rect = main.getBoundingClientRect();
  bounds.left = Math.max(bounds.left, rect.left);
  bounds.right = Math.min(bounds.right, rect.right);
  // En escritorio se desplaza el <main> y la cabecera es la barra lateral: solo cuenta el ancho.
  if (getComputedStyle(main).overflowY === "auto") return bounds;
  const header = document.querySelector("header");
  if (header) bounds.top = Math.max(bounds.top, header.getBoundingClientRect().bottom);
  const nav = document.querySelector('nav[aria-label="Secciones"]');
  if (nav && getComputedStyle(nav).position === "fixed") {
    bounds.bottom = Math.min(bounds.bottom, nav.getBoundingClientRect().top);
  }
  return bounds;
}
