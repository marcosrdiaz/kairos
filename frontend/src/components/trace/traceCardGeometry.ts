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
 * cabe y arriba hay más sitio. Nunca sale de `bounds` (el área donde vive la cifra: el contenido o
 * el panel del asistente, sin barra lateral, cabecera ni barra inferior). Si se pasa `avoid` (el
 * botón flotante del chat), la tarjeta no se solapa con él: se corre a su izquierda y, si no
 * cabe, se queda por encima de él. Solo geometría: no mide ni toca el DOM.
 */
export function placeCard(
  anchor: Box,
  size: { width: number; height: number },
  bounds: Box,
  avoid?: Box | null,
): CardPlacement {
  const width = Math.max(0, Math.min(size.width, bounds.right - bounds.left));
  let left = Math.max(bounds.left, Math.min(anchor.left, bounds.right - width));
  const below = Math.max(0, bounds.bottom - anchor.bottom - GAP_PX);
  const above = Math.max(0, anchor.top - bounds.top - GAP_PX);
  const side = size.height <= below || below >= above ? "below" : "above";
  let maxHeight = side === "below" ? below : above;
  const height = () => Math.min(size.height, maxHeight);
  const top = () => (side === "below" ? anchor.bottom + GAP_PX : anchor.top - GAP_PX - height());
  const box = (): Box => ({ left, top: top(), right: left + width, bottom: top() + height() });

  if (avoid && overlaps(box(), avoid)) {
    const shifted = avoid.left - GAP_PX - width;
    if (shifted >= bounds.left) left = shifted;
    else if (side === "below" && avoid.top > anchor.bottom) {
      maxHeight = Math.max(0, Math.min(maxHeight, avoid.top - GAP_PX - (anchor.bottom + GAP_PX)));
    }
  }
  return { left, top: top(), width, maxHeight, side };
}

/** ¿Se ve algo de la cifra dentro del área de contenido? */
export function overlaps(a: Box, b: Box): boolean {
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}

/**
 * Área donde se coloca la tarjeta de una cifra, leída del DOM de `AppShell`.
 * - Si la cifra está en el panel del asistente (`#asistente`), el propio panel: en escritorio es
 *   una columna a la derecha del contenido y en móvil, un modal a pantalla completa.
 * - Si no, el ancho de `<main id="contenido">` (deja fuera la barra lateral y el chat) y, en
 *   móvil, entre la cabecera fija y la barra de navegación inferior.
 * Sin `AppShell` (tests, `/lab`), la ventana entera. El botón flotante no recorta el área: se
 * esquiva aparte (`launcherBox`).
 */
export function contentBounds(anchor?: Element | null): Box {
  const bounds: Box = { left: 0, top: 0, right: window.innerWidth, bottom: window.innerHeight };
  const chat = document.getElementById("asistente");
  if (anchor && chat?.contains(anchor)) {
    const rect = chat.getBoundingClientRect();
    return {
      left: Math.max(bounds.left, rect.left),
      top: Math.max(bounds.top, rect.top),
      right: Math.min(bounds.right, rect.right),
      bottom: Math.min(bounds.bottom, rect.bottom),
    };
  }
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

/** El botón flotante del chat, mientras se ve (`null` si no está o está oculto). */
export function launcherBox(): Box | null {
  const launcher = document.getElementById("chat-launcher");
  if (!launcher || getComputedStyle(launcher).opacity === "0") return null;
  const { left, top, right, bottom } = launcher.getBoundingClientRect();
  return { left, top, right, bottom };
}
