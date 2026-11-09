import { useEvents } from "../../api/hooks/useEvents";
import { EmptyNote } from "../../components/PageTitle";
import { PanelSection } from "../PanelSection";
import { EventCard } from "./EventCard";

const TITLE = "Eventos";
const INTRO = "Lo que ha pasado en el mundo y cuánto te toca en euros. Solo salen los que afectan a tu cartera.";

/** Eventos de la cartera, del más reciente al más antiguo. Sin eventos, no se inventa nada. */
export function EventsSection({ portfolioId }: { portfolioId: string }) {
  const { data, isPending } = useEvents(portfolioId);

  return (
    <PanelSection id="eventos" title={TITLE} intro={INTRO} step={1}>
      {isPending && (
        <div
          role="status"
          aria-label="Cargando los eventos"
          className="h-48 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse"
        />
      )}
      {!isPending && !data && (
        <EmptyNote>
          Ahora mismo no podemos mostrar los eventos. Vuelve a intentarlo en unos segundos.
        </EmptyNote>
      )}
      {data && data.length === 0 && (
        <EmptyNote>
          Ningún evento reciente afecta a tu cartera. El silencio también es información.
        </EmptyNote>
      )}
      {data && data.length > 0 && (
        <div className="flex flex-col gap-4">
          {data.map((event) => (
            <EventCard key={event.event_id} event={event} />
          ))}
        </div>
      )}
    </PanelSection>
  );
}
