import { Link, useParams, useSearchParams } from "react-router";
import { PageTitle } from "../../../components/PageTitle";
import { usePortfolioId } from "../../portfolio-picker/usePortfolioId";
import { AssetChart } from "./AssetChart";

/** `/activo/:assetId?p=`: evolución de una posición (T2-23), enlazada desde el ticker y el panel. */
export function AssetPage() {
  const { assetId = "" } = useParams();
  const [params] = useSearchParams();
  const [portfolioId] = usePortfolioId();
  const query = params.toString() ? `?${params.toString()}` : "";
  return (
    <>
      <PageTitle visuallyHidden>Evolución de una posición</PageTitle>
      <div className="flex flex-col gap-4">
        <Link to={`/inicio${query}`} className="inline-flex min-h-touch w-fit items-center text-base font-semibold text-accent hover:underline">
          ← Volver a Inicio
        </Link>
        <AssetChart key={`${portfolioId}/${assetId}`} portfolioId={portfolioId} assetId={assetId} />
      </div>
    </>
  );
}
