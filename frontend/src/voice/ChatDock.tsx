/**
 * El asistente, siempre a mano en todas las pantallas de AppShell:
 *
 * - `ChatLauncher`: botón flotante abajo a la derecha con el logo del asistente (`ChatLogo`).
 *   En móvil queda por encima de las pestañas. Desaparece mientras el asistente está abierto.
 * - `ChatPanel`: en escritorio (≥ lg), una columna a la derecha que estrecha el contenido (la
 *   barra lateral no cambia); en móvil, un modal a pantalla completa por encima de todo.
 *   Está siempre montado: la conversación sigue ahí al cerrarlo y al navegar. Cerrado es
 *   `inert` (fuera del orden de foco y del lector). Al abrir, el foco va al campo de texto; al
 *   cerrar, vuelve al botón flotante.
 */
import { useEffect, useRef } from "react";
import { Navigate, useLocation } from "react-router";
import { usePortfolioId } from "../app/portfolio-picker/usePortfolioId";
import { ChatLogo } from "./ChatLogo";
import { useChatDock } from "./chatDockContext";
import { CHAT_TITLE_ID, VoiceAsk } from "./VoiceAsk";

/** `/pregunta` (enlaces antiguos y el atajo de Inicio): abre el asistente y vuelve a Inicio. */
export function OpenChatRoute() {
  const { setOpen } = useChatDock();
  const { search } = useLocation();
  useEffect(() => setOpen(true), [setOpen]);
  return <Navigate to={`/inicio${search}`} replace />;
}

export function ChatLauncher() {
  const { open, setOpen } = useChatDock();
  return (
    <button
      type="button"
      id="chat-launcher"
      onClick={() => setOpen(true)}
      aria-label="Abrir el asistente: pregunta a Kairos por texto o por voz"
      aria-expanded={open}
      aria-controls="asistente"
      tabIndex={open ? -1 : 0}
      className={`chat-launcher fixed bottom-[calc(var(--kairos-bottom-nav-height)+1rem)] right-4 z-30 grid size-20 cursor-pointer place-items-center rounded-full transition-[opacity,scale,translate,box-shadow] duration-200 ease-out hover:-translate-y-0.5 active:scale-95 lg:bottom-7 lg:right-7 lg:size-22 ${
        open ? "pointer-events-none scale-75 opacity-0" : "scale-100 opacity-100"
      }`}
    >
      <ChatLogo outlined className="size-14 translate-y-0.5 lg:size-15" />
    </button>
  );
}

export function ChatPanel() {
  const { open, setOpen } = useChatDock();
  const [portfolioId] = usePortfolioId();
  const panel = useRef<HTMLElement>(null);
  const wasOpen = useRef(open);

  useEffect(() => {
    const root = document.documentElement;
    if (open) {
      root.dataset.chatOpen = "";
      panel.current?.querySelector<HTMLTextAreaElement>("#ask-text")?.focus({ preventScroll: true });
    } else {
      delete root.dataset.chatOpen;
      if (wasOpen.current) document.getElementById("chat-launcher")?.focus();
    }
    wasOpen.current = open;
  }, [open]);

  return (
    <aside
      ref={panel}
      id="asistente"
      aria-labelledby={CHAT_TITLE_ID}
      inert={!open}
      className={[
        // Móvil: modal a pantalla completa.
        "fixed inset-0 z-50 overflow-hidden bg-paper transition-[opacity,translate,visibility] duration-300 ease-out",
        open ? "visible translate-y-0 opacity-100" : "invisible translate-y-6 opacity-0",
        // Escritorio: tercera columna de AppShell, con su propio alto.
        "lg:static lg:z-10 lg:h-dvh lg:translate-y-0 lg:opacity-100",
      ].join(" ")}
    >
      {/* Ancho fijo dentro de la columna que se abre: el contenido se revela, no se recoloca. El
          borde va aquí dentro para que, cerrada (columna de 0), no asome 1 px de scroll. */}
      <div className="h-full w-full lg:w-(--kairos-chat-width) lg:border-l lg:border-line">
        <VoiceAsk key={portfolioId} portfolioId={portfolioId} onClose={() => setOpen(false)} />
      </div>
    </aside>
  );
}
