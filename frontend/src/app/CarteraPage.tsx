import { PageTitle } from "../components/PageTitle";
import { DcaSection } from "./dca/DcaSection";
import { OperationsSection } from "./operations/OperationsSection";
import { OnboardingSection } from "./onboarding/OnboardingSection";
import { DemoReset } from "./portfolio-picker/DemoReset";
import { PortfolioPicker } from "./portfolio-picker/PortfolioPicker";

export function CarteraPage() {
  return (
    <>
      <PageTitle>Cartera</PageTitle>
      <div className="flex max-w-3xl flex-col gap-10">
        <section aria-labelledby="examples-title" className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h2 id="examples-title" className="m-0 text-xl font-semibold text-ink">
              Carteras de ejemplo
            </h2>
            <p className="m-0 text-base text-ink-muted">
              Laura y Javier son carteras ilustrativas para probar Kairos. Elige con cuál trabajar.
            </p>
          </div>
          <PortfolioPicker />
          <DemoReset />
        </section>
        <OperationsSection />
        <DcaSection />
        <OnboardingSection />
      </div>
    </>
  );
}
