import { useState } from "react";
import { useEvents } from "../../api/hooks/useEvents";
import type { EventType } from "../../app/news/labels";
import { EmptyNote } from "../../components/PageTitle";
import { PanelSection } from "../PanelSection";
import { EventCard } from "./EventCard";
import { EventFilter, type EventFilterValue } from "./EventFilter";

const TITLE = "Eventos";
const INTRO = "Lo que ha pasado en el mundo y cuánto te toca en euros. Solo salen los que afectan a tu cartera.";

/** Eventos de la cartera, del más reciente al más antiguo. Sin eventos, no se inventa nada. */
export function EventsSection({ portfolioId }: { portfolioId: string }) {
  const { data, isPending } = useEvents(portfolioId);
  const [filter, setFilter] = useState<EventFilterValue>("all");

  const types = [...new Set((data ?? []).map((e) => e.event_type))] as EventType[];
  // Si el tipo elegido deja de existir (la consulta se refresca sola), se vuelve a "Todos".
  const active: EventFilterValue = filter === "all" || types.includes(filter) ? filter : "all";
  const visible = (data ?? []).filter((e) => active === "all" || e.event_type === active);

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
        <>
          {types.length > 1 && (
            <EventFilter
              types={types}
              value={active}
              onChange={setFilter}
              shown={visible.length}
              total={data.length}
            />
          )}
          {/* `key` por filtro: la lista se vuelve a montar con un fundido corto (solo opacidad). */}
          <div key={active} className="panel-fade flex flex-col gap-4">
            {visible.map((event) => (
              <EventCard key={event.event_id} event={event} />
            ))}
          </div>
        </>
      )}
    </PanelSection>
  );
}
