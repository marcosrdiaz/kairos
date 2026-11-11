import { usePortfolioId } from "../app/portfolio-picker/usePortfolioId";
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
    <div className="flex w-full min-w-0 flex-col gap-10">
      {/* Título y barra de bloques: hijos directos para que la barra quede fija en todo el panel. */}
      <PanelHeader portfolioId={portfolioId} />
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
