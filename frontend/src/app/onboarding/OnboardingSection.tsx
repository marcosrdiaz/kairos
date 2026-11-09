import { usePortfolioId } from "../portfolio-picker/usePortfolioId";
import { usePortfolios } from "../portfolio-picker/usePortfolios";
import { OnboardingForm } from "./OnboardingForm";

/** Bloque "Añadir posiciones" de Cartera, sobre la cartera elegida en `?p=`. */
export function OnboardingSection() {
  const [portfolioId] = usePortfolioId();
  const { data } = usePortfolios();
  const name = data?.find((p) => p.id === portfolioId)?.name;
  return (
    <section aria-labelledby="onboarding-title" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 id="onboarding-title" className="m-0 text-xl font-semibold text-ink">
          Añadir posiciones{name ? ` a la cartera de ${name}` : ""}
        </h2>
        <p className="m-0 text-base text-ink-muted">
          Busca cada fondo, ETF o acción por su ISIN, ticker o nombre. Del resto (tipo, divisa,
          clase, comisión y si es traspasable) nos encargamos nosotros.
        </p>
      </div>
      <OnboardingForm key={portfolioId} portfolioId={portfolioId} />
    </section>
  );
}
