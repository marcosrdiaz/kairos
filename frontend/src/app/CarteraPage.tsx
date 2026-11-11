import { PageTitle } from "../components/PageTitle";
import { SwipeTabs } from "../ui/SwipeTabs";
import { DcaSection } from "./dca/DcaSection";
import { OperationsSection } from "./operations/OperationsSection";
import { OnboardingSection } from "./onboarding/OnboardingSection";
import { DemoReset } from "./portfolio-picker/DemoReset";
import { PortfolioManager } from "./portfolio-picker/PortfolioManager";
import { PortfolioPicker } from "./portfolio-picker/PortfolioPicker";

export function CarteraPage() {
  return (
    <>
      <PageTitle>Cartera</PageTitle>
      <div className="flex max-w-3xl flex-col gap-10">
        <section aria-labelledby="portfolios-title" className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h2 id="portfolios-title" className="m-0 text-xl font-semibold text-ink">
              Carteras
            </h2>
            <p className="m-0 text-base text-ink-muted">
              Cada cartera va por separado. Elige con cuál trabajar: Kairos la recuerda en este
              navegador y todas las pantallas muestran sus datos.
            </p>
          </div>
          <PortfolioPicker />
          <PortfolioManager />
          <DemoReset />
        </section>
        <SwipeTabs
          label="Secciones de la cartera"
          swipeable={false}
          items={[
            { id: "operations", title: "Operaciones", content: <OperationsSection /> },
            { id: "dca", title: "Aportaciones periódicas", content: <DcaSection /> },
            { id: "onboarding", title: "Añadir posiciones", content: <OnboardingSection /> },
          ]}
        />
      </div>
    </>
  );
}
