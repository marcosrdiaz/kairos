import type { ComponentType } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { BrandBanner } from "../components/BrandBanner";
import { ChatIcon, HomeIcon, LogoTile, PanelIcon, WalletIcon } from "../components/icons";
import { ThemeToggle } from "../theme/ThemeToggle";

const TABS: { to: string; label: string; Icon: ComponentType<{ className?: string }> }[] = [
  { to: "/inicio", label: "Inicio", Icon: HomeIcon },
  { to: "/cartera", label: "Cartera", Icon: WalletIcon },
  { to: "/pregunta", label: "Pregunta", Icon: ChatIcon },
];

/**
 * Marco de la app, adaptable (DESIGN.md § Layout):
 * - Móvil (< lg): cabecera con la marca y el modo oscuro; pestañas con icono fijas abajo.
 * - Escritorio (≥ lg): barra lateral con la marca, las secciones, el panel y el modo oscuro.
 * Hay un único <nav aria-label="Secciones">, recolocado con CSS, para no duplicarlo en el lector.
 * NavLink pone aria-current="page" en la sección activa. Conserva `?p=` al navegar.
 */
export function AppShell() {
  const { search } = useLocation();
  return (
    <div className="min-h-dvh bg-paper lg:grid lg:grid-cols-[var(--kairos-sidebar-width)_minmax(0,1fr)]">
      <header className="sticky top-0 z-20 flex h-(--kairos-header-height) items-center gap-3 border-b border-line bg-surface px-4 lg:h-dvh lg:flex-col lg:items-stretch lg:gap-6 lg:border-b-0 lg:border-r lg:bg-surface-muted lg:px-4 lg:pb-6 lg:pt-0">
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
          <ul className="m-0 flex list-none p-0 lg:flex-col lg:gap-1">
            {TABS.map(({ to, label, Icon }) => (
              <li key={to} className="flex flex-1 lg:flex-none">
                <NavLink
                  to={`${to}${search}`}
                  className={({ isActive }) =>
                    [
                      "flex flex-1 flex-col items-center justify-center gap-1 py-2 text-sm font-medium no-underline transition-colors",
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
                        <Icon className="size-6" />
                      </span>
                      {label}
                    </>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <Link
          to={`/panel${search}`}
          className="hidden min-h-touch items-center gap-3 rounded-control px-4 text-base font-medium text-ink-muted no-underline hover:bg-surface hover:text-ink lg:flex"
        >
          <PanelIcon className="size-6" />
          Panel de contexto
        </Link>

        <div className="ml-auto lg:hidden">
          <ThemeToggle />
        </div>
        <div className="hidden lg:mt-auto lg:block">
          <ThemeToggle showLabel />
        </div>
      </header>

      <main
        id="contenido"
        className="mx-auto w-full max-w-xl px-4 pb-[calc(var(--kairos-bottom-nav-height)+1.5rem)] pt-6 lg:max-w-none lg:px-10 lg:pb-12 lg:pt-10 2xl:px-14"
      >
        <Outlet />
      </main>
    </div>
  );
}
