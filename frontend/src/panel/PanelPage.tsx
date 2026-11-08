import { Link } from "react-router";
import { EmptyNote, PageTitle } from "../components/PageTitle";

/** Panel de contexto: layout de escritorio, sin pestañas inferiores. */
export function PanelPage() {
  return (
    <div className="min-h-dvh bg-paper">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-xl font-semibold text-accent">KAIROS</span>
          <Link to="/inicio" className="inline-flex min-h-touch items-center text-accent underline">
            Volver a la app
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <PageTitle>Panel de contexto</PageTitle>
        <EmptyNote>Aquí irán el resumen, los eventos, la exposición, el radar y la agenda.</EmptyNote>
      </main>
    </div>
  );
}
