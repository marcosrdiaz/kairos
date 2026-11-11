import { useMemo, useRef, useState, useSyncExternalStore, type ComponentType } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { BrandBanner } from "../components/BrandBanner";
import { AppNotice } from "../components/notices/Notices";
import { Scrollbar } from "../components/Scrollbar";
import { HomeIcon, LogoTile, PanelIcon, WalletIcon } from "../components/icons";
import { ThemeToggle } from "../theme/ThemeToggle";
import { ChatLauncher, ChatPanel } from "../voice/ChatDock";
import { ChatDockContext } from "../voice/chatDockContext";
import { AlertsNavIcon } from "./alerts/AlertsNavIcon";
import { NewsIcon } from "./news-feed/NewsIcon";
import { FirstRunGate } from "./onboarding/FirstRunGate";

const TABS: { to: string; label: string; Icon: ComponentType<{ className?: string }> }[] = [
  { to: "/inicio", label: "Inicio", Icon: HomeIcon },
  { to: "/cartera", label: "Cartera", Icon: WalletIcon },
  { to: "/noticias", label: "Noticias", Icon: NewsIcon },
  { to: "/alertas", label: "Avisos", Icon: AlertsNavIcon },
  { to: "/panel", label: "Panel de contexto", Icon: PanelIcon },
];

const DESKTOP = "(min-width: 64rem)";

/** Si la pantalla es de escritorio (≥ lg): ahí el asistente es un panel, no un modal. */
function useIsDesktop(): boolean {
  return useSyncExternalStore(
    (notify) => {
      if (typeof window.matchMedia !== "function") return () => undefined;
      const query = window.matchMedia(DESKTOP);
      query.addEventListener("change", notify);
      return () => query.removeEventListener("change", notify);
    },
    () => typeof window.matchMedia === "function" && window.matchMedia(DESKTOP).matches,
  );
}

/**
 * Marco de la app, adaptable (DESIGN.md § Layout):
 * - Móvil (< lg): cabecera con la marca y el modo oscuro; pestañas con icono fijas abajo.
 * - Escritorio (≥ lg): barra lateral con la marca, cinco secciones y el modo oscuro.
 * Hay un único <nav aria-label="Secciones">, recolocado con CSS, para no duplicarlo en el lector.
 * NavLink pone aria-current="page" en la sección activa. Conserva `?p=` al navegar.
 * El asistente (Pregunta) no es una sección: es el botón flotante y su panel (`voice/ChatDock`).
 * En escritorio abre una tercera columna que estrecha el contenido; en móvil, un modal que deja
 * el resto de la app `inert` mientras está abierto.
 * El contenido ocupa el ancho disponible en todos los tamaños; cada pantalla limita localmente
 * solo las zonas de lectura o formularios que lo necesitan. En escritorio la ventana no se
 * desplaza: lo hace el <main>, con la barra de scroll propia (`components/Scrollbar`).
 */
export function AppShell() {
  const { search } = useLocation();
  const [chatOpen, setChatOpen] = useState(false);
  const dock = useMemo(() => ({ open: chatOpen, setOpen: setChatOpen }), [chatOpen]);
  const desktop = useIsDesktop();
  const modal = chatOpen && !desktop;
  const mainRef = useRef<HTMLElement>(null);
  return (
    <FirstRunGate>
    <ChatDockContext value={dock}>
    <div
      className={`min-h-dvh bg-paper lg:grid lg:h-dvh lg:overflow-hidden lg:transition-[grid-template-columns] lg:duration-300 lg:ease-out motion-reduce:transition-none ${
        chatOpen
          ? "lg:grid-cols-[var(--kairos-sidebar-width)_minmax(0,1fr)_var(--kairos-chat-width)]"
          : "lg:grid-cols-[var(--kairos-sidebar-width)_minmax(0,1fr)_0rem]"
      }`}
    >
      {/* Primer elemento con foco: salta la cabecera y la navegación (WCAG 2.4.1). */}
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-30 focus:rounded-full focus:bg-accent focus:px-5 focus:py-3 focus:text-base focus:font-semibold focus:text-on-accent"
      >
        Saltar al contenido
      </a>
      <header inert={modal} className="sticky top-0 z-20 flex h-(--kairos-header-height) items-center gap-3 border-b border-line bg-surface px-4 lg:h-dvh lg:flex-col lg:items-stretch lg:gap-6 lg:border-b-0 lg:border-r lg:bg-surface-muted lg:px-4 lg:pb-6 lg:pt-0">
        {/* Móvil: logo compacto. Escritorio: banner de marca a sangre en la cabecera de la barra. */}
        <Link
          to={`/inicio${search}`}
          className="flex min-h-touch items-center gap-2 text-xl font-semibold tracking-tight text-ink no-underline lg:hidden"
        >
          <LogoTile className="size-10" />
          Kairos
        </Link>
        <Link
          to={`/inicio${search}`}
          aria-label="Kairos, ir a Inicio"
          className="-mx-4 hidden border-b border-line no-underline lg:block"
        >
          <BrandBanner />
        </Link>

        <nav
          aria-label="Secciones"
          className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] lg:static lg:border-t-0 lg:border-b lg:bg-transparent lg:pb-6"
        >
          <ul className="m-0 flex min-h-22 list-none p-0 lg:min-h-0 lg:flex-col lg:gap-1">
            {TABS.map(({ to, label, Icon }) => (
              <li key={to} className="flex flex-1 lg:flex-none">
                <NavLink
                  to={`${to}${search}`}
                  className={({ isActive }) =>
                    [
                      "flex min-w-0 flex-1 flex-col items-center justify-center gap-1 py-2 text-center text-xs font-medium leading-tight no-underline transition-colors sm:text-sm",
                      "lg:min-h-touch lg:flex-row lg:justify-start lg:gap-3 lg:rounded-control lg:px-4 lg:py-2.5 lg:text-base",
                      isActive
                        ? "text-accent lg:bg-accent lg:text-on-accent"
                        : "text-ink-muted hover:text-ink lg:hover:bg-surface",
                    ].join(" ")
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span
                        className={`flex h-8 w-14 items-center justify-center rounded-full lg:h-auto lg:w-auto ${isActive ? "bg-accent-tint lg:bg-transparent" : ""}`}
                      >
                        <Icon className="size-5 lg:size-6" />
                      </span>
                      {label}
                    </>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="ml-auto flex items-center gap-2 lg:hidden">
          <ThemeToggle />
        </div>
        <div className="hidden lg:mt-auto lg:block">
          <ThemeToggle showLabel />
        </div>
      </header>

      <div className="min-w-0 lg:relative lg:h-dvh">
        <main
          ref={mainRef}
          id="contenido"
          tabIndex={-1}
          inert={modal}
          className="outline-none @container/app-content mx-auto min-w-0 w-full px-4 pb-[calc(var(--kairos-bottom-nav-height)+7.5rem)] pt-6 kairos-scroll lg:h-dvh lg:overflow-y-auto lg:scroll-pb-4 lg:scroll-pt-4 lg:px-10 lg:pb-36 lg:pt-10 2xl:px-14"
        >
          <Outlet />
          <AppNotice />
        </main>
        <Scrollbar target={mainRef} className="hidden lg:flex" />
      </div>

      <ChatPanel />
      <ChatLauncher />
    </div>
    </ChatDockContext>
    </FirstRunGate>
  );
}
