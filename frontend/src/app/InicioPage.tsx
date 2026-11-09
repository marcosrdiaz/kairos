import { Link, useSearchParams } from "react-router";
import { EmptyNote, PageTitle } from "../components/PageTitle";
import { StatusCard } from "../widget/StatusCard";
import { useStatus } from "../widget/useStatus";

const DEFAULT_PORTFOLIO = "laura";

/** Esqueleto de carga: misma forma que la tarjeta, sin cifras. */
function StatusSkeleton() {
  return (
    <div
      role="status"
      aria-label="Cargando el estado de tu cartera"
      className="rounded-card border border-line bg-surface p-5 lg:p-8"
    >
      <div className="flex flex-col gap-4 motion-safe:animate-pulse">
        <div className="h-6 w-40 rounded bg-line" />
        <div className="h-12 w-64 max-w-full rounded bg-line" />
        <div className="h-5 w-full max-w-md rounded bg-line" />
      </div>
    </div>
  );
}

function Shortcut({ to, title, text }: { to: string; title: string; text: string }) {
  return (
    <Link
      to={to}
      className="flex min-h-touch flex-col gap-1 rounded-card border border-line bg-surface p-4 no-underline hover:border-line-strong"
    >
      <span className="text-lg font-semibold text-accent">{title}</span>
      <span className="text-base text-ink-muted">{text}</span>
    </Link>
  );
}

export function InicioPage() {
  const [params] = useSearchParams();
  const portfolioId = params.get("p") || DEFAULT_PORTFOLIO;
  const { data, isPending, isError } = useStatus(portfolioId);
  const query = params.toString() ? `?${params.toString()}` : "";

  return (
    <>
      <PageTitle>Inicio</PageTitle>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:items-start">
        <div>
          {isPending && <StatusSkeleton />}
          {isError && (
            <EmptyNote>
              Ahora mismo no podemos mostrar el estado de tu cartera. Vuelve a intentarlo en unos
              segundos.
            </EmptyNote>
          )}
          {data && <StatusCard status={data} detailHref={`/panel${query}`} />}
        </div>
        <nav aria-label="Atajos" className="flex flex-col gap-3">
          <Shortcut
            to={`/pregunta${query}`}
            title="Pregunta a KAIROS"
            text="Por voz o por escrito: qué le pasa a tu cartera y por qué."
          />
          <Shortcut
            to={`/cartera${query}`}
            title="Tu cartera"
            text="Posiciones, operaciones y aportaciones periódicas."
          />
          <Shortcut
            to={`/panel${query}`}
            title="Panel de contexto"
            text="Eventos, exposición y agenda con más detalle."
          />
        </nav>
      </div>
    </>
  );
}
