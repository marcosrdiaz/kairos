import { Link, NavLink, Outlet, useLocation } from "react-router";

const TABS = [
  { to: "/inicio", label: "Inicio" },
  { to: "/cartera", label: "Cartera" },
  { to: "/pregunta", label: "Pregunta" },
] as const;

/**
 * Marco de la app, adaptable:
 * - Móvil (< lg): columna centrada y tres pestañas fijas abajo.
 * - Escritorio (≥ lg): barra superior con la marca, las pestañas y el enlace al panel;
 *   contenido más ancho.
 * Es un único <nav>: en escritorio sube arriba con `order`, así no se duplica para el lector de pantalla.
 * Conserva `?p=` (cartera elegida) al cambiar de pestaña.
 */
export function AppShell() {
  const { search } = useLocation();
  return (
    <div className="flex min-h-dvh flex-col bg-paper">
      <main className="mx-auto w-full max-w-xl flex-1 px-4 pb-6 pt-6 lg:max-w-6xl lg:px-6 lg:pb-12 lg:pt-10">
        <Outlet />
      </main>
      <nav
        aria-label="Secciones"
        className="sticky bottom-0 border-t border-line bg-surface lg:top-0 lg:bottom-auto lg:-order-1 lg:border-b lg:border-t-0"
      >
        <div className="mx-auto flex max-w-xl items-stretch lg:max-w-6xl lg:gap-8 lg:px-6">
          <Link
            to={`/inicio${search}`}
            className="hidden items-center text-xl font-semibold tracking-wide text-accent no-underline lg:flex"
          >
            KAIROS
          </Link>
          <ul className="m-0 flex flex-1 list-none p-0 lg:flex-none lg:gap-2">
            {TABS.map((t) => (
              <li key={t.to} className="flex-1 lg:flex-none">
                <NavLink
                  to={`${t.to}${search}`}
                  className={({ isActive }) =>
                    [
                      "flex min-h-14 items-center justify-center border-t-4 px-2 text-base font-medium no-underline",
                      "lg:min-h-16 lg:border-t-0 lg:border-b-4 lg:px-4",
                      isActive
                        ? "border-accent bg-paper text-accent lg:bg-transparent"
                        : "border-transparent text-ink-muted hover:text-ink",
                    ].join(" ")
                  }
                >
                  {t.label}
                </NavLink>
              </li>
            ))}
          </ul>
          <Link
            to={`/panel${search}`}
            className="ml-auto hidden min-h-touch items-center self-center font-medium text-accent underline lg:inline-flex"
          >
            Panel de contexto
          </Link>
        </div>
      </nav>
    </div>
  );
}
