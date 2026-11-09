import type { AgendaItemOut, Factor } from "../../api/generated/schema";
import { useAgenda } from "../../api/hooks/useAgenda";
import { EVENT_TYPE_LABEL } from "../../app/news/labels";
import { EmptyNote } from "../../components/PageTitle";
import { formatDate, formatEur, formatPercent } from "../../lib/format";
import { PanelSection } from "../PanelSection";
import { Traced } from "../Traced";

const TITLE = "Agenda";
const INTRO = "Lo que viene y cuánto de tu cartera depende de ello.";

/** Factor de mercado en palabras de inversor. */
const FACTOR_LABEL: Record<Factor, string> = {
  EQ_GLOBAL: "la bolsa mundial",
  EQ_US_TECH: "las tecnológicas de EE. UU.",
  RATES_EUR: "los tipos de interés del euro",
  OIL: "el petróleo",
  EURUSD: "el cambio euro-dólar",
};

function kindLabel(kind: AgendaItemOut["kind"]): string {
  return kind === "dca" ? "Tu plan" : EVENT_TYPE_LABEL[kind];
}

function AgendaRow({ item }: { item: AgendaItemOut }) {
  return (
    <li className="grid gap-x-6 gap-y-2 rounded-card border border-line bg-surface p-5 sm:grid-cols-[11rem_minmax(0,1fr)_auto] sm:items-center">
      <p className="m-0 text-base font-semibold tabular-nums text-ink">
        <time dateTime={item.date}>{formatDate(item.date)}</time>
      </p>
      <div className="min-w-0">
        <p className="m-0 text-sm font-semibold text-accent">{kindLabel(item.kind)}</p>
        <h3 className="m-0 text-lg font-semibold leading-snug text-ink">{item.title}</h3>
        {item.factor && (
          <p className="m-0 mt-1 text-base text-ink-muted">
            Tu cartera depende de {FACTOR_LABEL[item.factor]}
            {item.exposed_weight && (
              <>
                : un{" "}
                <span className="tabular-nums">
                  <Traced calcId={item.calc_id}>{formatPercent(item.exposed_weight)}</Traced>
                </span>
              </>
            )}
            .
          </p>
        )}
      </div>
      {item.exposed_eur && (
        <p className="m-0 text-base text-ink sm:text-right">
          <span className="block text-sm font-medium text-ink-muted">
            {item.kind === "dca" ? "Aportación prevista" : "Expuesto"}
          </span>
          <span className="text-lg font-semibold tabular-nums">
            <Traced calcId={item.calc_id}>{formatEur(item.exposed_eur, 0)}</Traced>
          </span>
        </p>
      )}
    </li>
  );
}

/** Agenda: lo que muestre el backend, sin añadir nada. Con la agenda vacía, se dice. */
export function AgendaSection({ portfolioId }: { portfolioId: string }) {
  const { data, isPending } = useAgenda(portfolioId);

  return (
    <PanelSection id="agenda" title={TITLE} intro={INTRO} step={4}>
      {isPending && (
        <div
          role="status"
          aria-label="Cargando la agenda"
          className="h-28 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse"
        />
      )}
      {!isPending && !data && (
        <EmptyNote>
          Ahora mismo no podemos mostrar la agenda. Vuelve a intentarlo en unos segundos.
        </EmptyNote>
      )}
      {data && data.length === 0 && (
        <EmptyNote>No hay nada previsto en tu agenda por ahora.</EmptyNote>
      )}
      {data && data.length > 0 && (
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {data.map((item) => (
            <AgendaRow key={`${item.date}-${item.title}`} item={item} />
          ))}
        </ul>
      )}
    </PanelSection>
  );
}
