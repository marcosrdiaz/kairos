import { usePortfolioId } from "../app/portfolio-picker/usePortfolioId";
import { PageTitle } from "../components/PageTitle";
import { AgendaSection } from "./agenda/AgendaSection";
import { EventsSection } from "./events/EventsSection";
import { ExposureSection } from "./exposure/ExposureSection";
import "./panel.css";
import { PanelHeader } from "./PanelHeader";
import { PanelNoticeSlot } from "./PanelNoticeSlot";
import { RadarSection } from "./radar/RadarSection";
import { ScenariosSection } from "./scenarios/ScenariosSection";
import { SummarySection } from "./summary/SummarySection";

/**
 * Panel de contexto dentro de AppShell. La cartera sale de `?p=`; al cambiarla en Cartera,
 * los bloques se montan de nuevo y entran con su animación corta.
 */
export function PanelPage() {
  const [portfolioId] = usePortfolioId();
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
      <div className="flex flex-col gap-4">
        <PageTitle>Panel de contexto</PageTitle>
        <PanelHeader portfolioId={portfolioId} />
      </div>
      <PanelNoticeSlot />
      <SummarySection key={`resumen-${portfolioId}`} portfolioId={portfolioId} />
      <EventsSection key={`eventos-${portfolioId}`} portfolioId={portfolioId} />
      <ExposureSection key={`exposicion-${portfolioId}`} portfolioId={portfolioId} />
      <RadarSection key={`radar-${portfolioId}`} portfolioId={portfolioId} />
      <AgendaSection key={`agenda-${portfolioId}`} portfolioId={portfolioId} />
      <ScenariosSection key={`escenarios-${portfolioId}`} portfolioId={portfolioId} />
    </div>
  );
}
