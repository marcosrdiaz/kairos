import { usePortfolioId } from "../app/portfolio-picker/usePortfolioId";
import { PageTitle } from "../components/PageTitle";
import { EventsSection } from "./events/EventsSection";
import { ExposureSection } from "./exposure/ExposureSection";
import "./panel.css";
import { PanelHeader } from "./PanelHeader";
import { PanelNoticeSlot } from "./PanelNoticeSlot";
import { RadarSection } from "./radar/RadarSection";
import { SummarySection } from "./summary/SummarySection";

/**
 * Panel de contexto: layout de escritorio, sin pestañas inferiores. La cartera sale de `?p=`
 * (la cambia el selector de la cabecera); al cambiarla, los bloques se montan de nuevo y
 * entran con su animación corta.
 */
export function PanelPage() {
  const [portfolioId] = usePortfolioId();
  return (
    <div className="min-h-dvh bg-paper">
      <PanelHeader portfolioId={portfolioId} />
      <main className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-8">
        <PageTitle visuallyHidden>Panel de contexto</PageTitle>
        <PanelNoticeSlot />
        <SummarySection key={`resumen-${portfolioId}`} portfolioId={portfolioId} />
        <EventsSection key={`eventos-${portfolioId}`} portfolioId={portfolioId} />
        <ExposureSection key={`exposicion-${portfolioId}`} portfolioId={portfolioId} />
        <RadarSection key={`radar-${portfolioId}`} portfolioId={portfolioId} />
      </main>
    </div>
  );
}
