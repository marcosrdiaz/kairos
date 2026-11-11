import { useExposure } from "../../api/hooks/useExposure";
import { useLivePortfolio } from "../../api/hooks/useLivePortfolio";
import { EmptyNote } from "../../components/PageTitle";
import { formatDate, formatPercent } from "../../lib/format";
import { PanelSection } from "../PanelSection";
import { Traced } from "../Traced";
import { BucketBars } from "./BucketBars";
import { TopCompanies } from "./TopCompanies";

const TITLE = "Exposición";
const INTRO =
  "Qué hay realmente dentro de tu cartera, sumando lo que tienes directamente y lo que llevan tus fondos y ETF.";

/** Look-through: radiografía, reparto por país, sector y divisa, y mayores empresas. */
export function ExposureSection({ portfolioId }: { portfolioId: string }) {
  const { data, isPending } = useExposure(portfolioId);
  const portfolio = useLivePortfolio(portfolioId);

  return (
    <PanelSection id="exposicion" title={TITLE} intro={INTRO} step={2}>
      {isPending && (
        <div
          role="status"
          aria-label="Cargando la exposición"
          className="h-64 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse"
        />
      )}
      {!isPending && !data && (
        <EmptyNote>
          Ahora mismo no podemos mostrar la exposición. Vuelve a intentarlo en unos segundos.
        </EmptyNote>
      )}
      {data && (
        <div className="flex flex-col gap-4">
          <dl className="m-0 grid gap-4 rounded-card border border-line bg-surface p-6 sm:grid-cols-3">
            <div>
              <dt className="text-base font-medium text-ink-muted">Posiciones</dt>
              <dd className="m-0 mt-1 text-2xl font-semibold tabular-nums text-ink">
                {data.radiography.num_holdings}
              </dd>
            </div>
            <div>
              <dt className="text-base font-medium text-ink-muted">
                Mayor país: {data.radiography.top_country.label}
              </dt>
              <dd className="m-0 mt-1 text-2xl font-semibold tabular-nums text-ink">
                <Traced calcId={data.calc_id}>
                  {formatPercent(data.radiography.top_country.weight)}
                </Traced>
              </dd>
            </div>
            <div>
              <dt className="text-base font-medium text-ink-muted">
                Tus {data.radiography.top_companies_group.n} mayores empresas
              </dt>
              <dd className="m-0 mt-1 text-2xl font-semibold tabular-nums text-ink">
                <Traced calcId={data.calc_id}>
                  {formatPercent(data.radiography.top_companies_group.weight)}
                </Traced>
              </dd>
            </div>
          </dl>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <BucketBars title="Por país" buckets={data.by_country} calcId={data.calc_id} />
            <BucketBars title="Por sector" buckets={data.by_sector} calcId={data.calc_id} />
            <BucketBars title="Por divisa" buckets={data.by_currency} calcId={data.calc_id} />
          </div>

          <TopCompanies exposure={data} portfolio={portfolio.data} />

          <p className="m-0 text-sm text-ink-muted">
            Composición de los fondos y ETF cubierta: {formatPercent(data.coverage_pct)}. Datos a{" "}
            {formatDate(data.as_of)}.
          </p>
        </div>
      )}
    </PanelSection>
  );
}
