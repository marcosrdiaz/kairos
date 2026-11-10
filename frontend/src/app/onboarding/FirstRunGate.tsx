import { useState, type ReactNode } from "react";
import { useNavigate } from "react-router";
import { AppNotice } from "../../components/notices/Notices";
import { LogoTile } from "../../components/icons";
import { ThemeToggle } from "../../theme/ThemeToggle";
import { usePortfolios } from "../portfolio-picker/usePortfolios";
import { FirstRunWizard } from "./FirstRunWizard";

/**
 * Primer uso (T4-12): si `GET /portfolios` devuelve una lista vacía, en lugar de la app se
 * abre el asistente para crear la primera cartera. No hay pestañas ni otras pantallas hasta
 * terminarlo. Mientras carga o si falla la lista, se ve la app como siempre (cada pantalla
 * tiene su estado vacío o de error).
 *
 * El asistente se queda abierto hasta que termina, aunque la lista deje de estar vacía en
 * medio (al crear la cartera en el paso 1). Si más adelante se borra la última cartera,
 * vuelve a abrirse.
 */
export function FirstRunGate({ children }: { children: ReactNode }) {
  const { data, isSuccess } = usePortfolios();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const empty = isSuccess && data.length === 0;
  // Actualizar el estado durante el render es el patrón de React para derivarlo de los datos.
  if (empty && !open) setOpen(true);

  if (!open) return children;

  function done(portfolioId: string) {
    setOpen(false);
    void navigate(`/inicio?p=${encodeURIComponent(portfolioId)}`, { replace: true });
  }

  return (
    <div className="min-h-dvh bg-paper">
      <header className="flex h-(--kairos-header-height) items-center gap-3 border-b border-line bg-surface px-4 lg:px-10">
        <span className="flex items-center gap-2 text-xl font-semibold tracking-tight text-ink">
          <LogoTile className="size-10" />
          Kairos
        </span>
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </header>
      <main id="contenido" tabIndex={-1} className="mx-auto w-full max-w-2xl px-4 pb-12 pt-8 outline-none">
        <FirstRunWizard onDone={done} />
        <AppNotice />
      </main>
    </div>
  );
}
