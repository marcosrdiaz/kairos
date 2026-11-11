import { useSearchParams } from "react-router";
import { useStatus } from "../api/hooks/useStatus";
import { EmptyNote, PageTitle } from "../components/PageTitle";
import { PortfolioChart } from "./market/chart/PortfolioChart";
import { MarketTicker } from "./market/ticker/MarketTicker";
import { NewsSection } from "./news/NewsSection";
import { StatusCard } from "../widget/StatusCard";
import { StatusTiles } from "../widget/StatusTiles";
import { usePortfolioId } from "./portfolio-picker/usePortfolioId";
import "./inicio.css";

/** Esqueleto de carga de las tarjetas: misma forma que la columna, sin cifras. */
function StatusSkeleton() {
  return (
    <div role="status" aria-label="Cargando el estado de tu cartera" className="home-tiles">
      <div className="h-40 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse" />
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="h-12 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse"
        />
      ))}
    </div>
  );
}

export function InicioPage() {
  const [params] = useSearchParams();
  const [portfolioId] = usePortfolioId();
  const { data, isPending, isError } = useStatus(portfolioId);
  const query = params.toString() ? `?${params.toString()}` : "";

  return (
    <>
      <PageTitle visuallyHidden>Inicio</PageTitle>
      {/* Columna que ocupa el alto de la pantalla: el espacio que sobra va solo a la fila de la
          gráfica (`.home-top`); noticias, ticker y aviso se quedan con su alto natural. */}
      <div className="flex flex-col gap-4 lg:flex-1">
        <div className="home-top">
          <PortfolioChart key={portfolioId} portfolioId={portfolioId} />
          {isPending && <StatusSkeleton />}
          {isError && !data && (
            <EmptyNote>
              Ahora mismo no podemos mostrar el estado de tu cartera. Vuelve a intentarlo en unos
              segundos.
            </EmptyNote>
          )}
          {data && (
            <div className="home-tiles">
              <StatusCard status={data} detailHref={`/panel${query}`} />
              <StatusTiles status={data} />
            </div>
          )}
        </div>
        <NewsSection portfolioId={portfolioId} newsHref={`/noticias${query}`} />
        {/* En escritorio, el botón flotante del asistente queda sobre el borde derecho: la barra
            lo esquiva para que su pausa siga a la vista. */}
        <div className="lg:mr-20">
          <MarketTicker portfolioId={portfolioId} />
        </div>
      </div>
    </>
  );
}
