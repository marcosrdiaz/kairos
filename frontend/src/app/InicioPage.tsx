import type { ComponentType } from "react";
import { Link, useSearchParams } from "react-router";
import { useStatus } from "../api/hooks/useStatus";
import { ArrowRightIcon, ChatIcon, PanelIcon, WalletIcon } from "../components/icons";
import { EmptyNote, PageTitle } from "../components/PageTitle";
import { NewsSection } from "./news/NewsSection";
import { AlertNotice } from "../widget/AlertNotice";
import { StatusCard } from "../widget/StatusCard";
import { StatusTiles } from "../widget/StatusTiles";

const DEFAULT_PORTFOLIO = "laura";

/** Esqueleto de carga: misma forma que la cabecera y las tarjetas, sin cifras. */
function StatusSkeleton() {
  return (
    <div role="status" aria-label="Cargando el estado de tu cartera" className="flex flex-col gap-6">
      <div className="h-64 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse" />
      <div className="grid grid-cols-1 gap-4 min-[360px]:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-36 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse"
          />
        ))}
      </div>
    </div>
  );
}

const SHORTCUTS: {
  to: string;
  title: string;
  text: string;
  Icon: ComponentType<{ className?: string }>;
}[] = [
  {
    to: "/pregunta",
    title: "Pregunta a KAIROS",
    text: "Por voz o por escrito: qué le pasa a tu cartera y por qué.",
    Icon: ChatIcon,
  },
  {
    to: "/cartera",
    title: "Tu cartera",
    text: "Posiciones, operaciones y aportaciones periódicas.",
    Icon: WalletIcon,
  },
  {
    to: "/panel",
    title: "Panel de contexto",
    text: "Eventos, exposición y agenda con más detalle.",
    Icon: PanelIcon,
  },
];

function Shortcuts({ query }: { query: string }) {
  return (
    <section aria-labelledby="atajos-heading" className="rounded-card border border-line bg-surface p-5 lg:p-6">
      <h2 id="atajos-heading" className="m-0 mb-3 text-lg font-semibold text-ink">
        Qué puedes hacer
      </h2>
      <ul className="m-0 grid list-none gap-2 p-0 lg:grid-cols-3">
        {SHORTCUTS.map(({ to, title, text, Icon }) => (
          <li key={to} className="flex">
            <Link
              to={`${to}${query}`}
              className="group flex flex-1 items-start gap-4 rounded-control p-3 no-underline hover:bg-surface-muted"
            >
              <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-accent-tint text-accent">
                <Icon className="size-6" />
              </span>
              <span className="flex flex-1 flex-col gap-0.5">
                <span className="inline-flex items-center gap-1 text-base font-semibold text-accent group-hover:underline">
                  {title}
                  <ArrowRightIcon className="size-4" />
                </span>
                <span className="text-base text-ink-muted">{text}</span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function InicioPage() {
  const [params] = useSearchParams();
  const portfolioId = params.get("p") || DEFAULT_PORTFOLIO;
  const { data, isPending, isError } = useStatus(portfolioId);
  const query = params.toString() ? `?${params.toString()}` : "";

  return (
    <>
      <PageTitle visuallyHidden>Inicio</PageTitle>
      <div className="flex flex-col gap-6">
        <AlertNotice portfolioId={portfolioId} href={`/panel${query}`} />
        {isPending && <StatusSkeleton />}
        {isError && !data && (
          <EmptyNote>
            Ahora mismo no podemos mostrar el estado de tu cartera. Vuelve a intentarlo en unos
            segundos.
          </EmptyNote>
        )}
        {data && <StatusCard status={data} detailHref={`/panel${query}`} />}
        {/* Aquí irán el ticker de mercado (T2-17) y la gráfica interactiva (T2-18) cuando haya datos. */}
        {data && <StatusTiles status={data} />}
        <NewsSection portfolioId={portfolioId} panelHref={`/panel${query}`} />
        <Shortcuts query={query} />
      </div>
    </>
  );
}
