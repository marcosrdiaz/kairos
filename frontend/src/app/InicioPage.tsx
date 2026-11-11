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

/** Esqueleto de carga: misma forma que la cabecera y las tarjetas, sin cifras. */
function StatusSkeleton() {
  return (
    <div role="status" aria-label="Cargando el estado de tu cartera" className="flex flex-col gap-6">
      <div className="h-64 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse" />
      <div className="home-status-grid">
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

export function InicioPage() {
  const [params] = useSearchParams();
  const [portfolioId] = usePortfolioId();
  const { data, isPending, isError } = useStatus(portfolioId);
  const query = params.toString() ? `?${params.toString()}` : "";

  return (
    <>
      <PageTitle visuallyHidden>Inicio</PageTitle>
      <div className="flex flex-col gap-6">
        <PortfolioChart key={portfolioId} portfolioId={portfolioId} />
        {isPending && <StatusSkeleton />}
        {isError && !data && (
          <EmptyNote>
            Ahora mismo no podemos mostrar el estado de tu cartera. Vuelve a intentarlo en unos
            segundos.
          </EmptyNote>
        )}
        <MarketTicker portfolioId={portfolioId} />
        {data && (
          <div className="home-status-grid">
            <StatusCard status={data} detailHref={`/panel${query}`} />
            <StatusTiles status={data} />
          </div>
        )}
        <NewsSection portfolioId={portfolioId} newsHref={`/noticias${query}`} />
      </div>
    </>
  );
}
