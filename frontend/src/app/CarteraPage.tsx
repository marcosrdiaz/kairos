import { PageTitle } from "../components/PageTitle";
import { SwipeTabs } from "../ui/SwipeTabs";
import { DcaSection } from "./dca/DcaSection";
import { OperationsSection } from "./operations/OperationsSection";
import { PortfolioManager } from "./portfolio-picker/PortfolioManager";

/**
 * Cartera (armonizada en T5-15): primero con qué cartera se trabaja, con los círculos de perfil
 * en una tarjeta como las de Inicio, luego la gestión de carteras y las pestañas de T5-05.
 */
export function CarteraPage() {
  return (
    <>
      <PageTitle>Cartera</PageTitle>
      <div className="flex min-w-0 w-full flex-col gap-8">
        <p className="m-0 text-base text-ink-muted">
          Tus carteras, las operaciones que apuntas en cada una y sus aportaciones periódicas.
        </p>
        <section aria-labelledby="portfolios-title" className="flex flex-col gap-6">
          <div className="flex flex-col gap-4 rounded-card border border-line bg-surface p-5">
            <div className="flex flex-col gap-1">
              <h2 id="portfolios-title" className="m-0 text-xl font-semibold text-ink">
                Carteras
              </h2>
              <p className="m-0 text-base text-ink-muted">
                Cada cartera va por separado. Elige con cuál trabajar: Kairos la recuerda en este
                navegador y todas las pantallas muestran sus datos.
              </p>
            </div>
            <PortfolioManager pickerLabelledBy="portfolios-title" />
          </div>
        </section>
        <SwipeTabs
          label="Secciones de la cartera"
          swipeable={false}
          items={[
            { id: "operations", title: "Operaciones", content: <OperationsSection /> },
            { id: "dca", title: "Aportaciones periódicas", content: <DcaSection /> },
          ]}
        />
      </div>
    </>
  );
}
