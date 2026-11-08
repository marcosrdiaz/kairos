import { NavLink, Outlet } from "react-router";

const TABS = [
  { to: "/inicio", label: "Inicio" },
  { to: "/cartera", label: "Cartera" },
  { to: "/pregunta", label: "Pregunta" },
] as const;

/** Marco móvil: contenido arriba, pestañas abajo. En pantallas anchas se centra como una columna. */
export function AppShell() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col bg-paper">
      <main className="flex-1 px-4 pb-6 pt-6">
        <Outlet />
      </main>
      <nav aria-label="Secciones" className="sticky bottom-0 border-t border-line bg-surface">
        <ul className="m-0 flex list-none p-0">
          {TABS.map((t) => (
            <li key={t.to} className="flex-1">
              <NavLink
                to={t.to}
                className={({ isActive }) =>
                  [
                    "flex min-h-14 items-center justify-center border-t-4 px-2 text-base font-medium no-underline",
                    isActive
                      ? "border-accent bg-paper text-accent"
                      : "border-transparent text-ink-muted hover:text-ink",
                  ].join(" ")
                }
              >
                {t.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
