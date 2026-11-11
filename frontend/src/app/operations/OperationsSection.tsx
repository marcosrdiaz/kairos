import { CoinsIcon } from "../../components/icons";
import { usePortfolioId } from "../portfolio-picker/usePortfolioId";
import { OperationsForm } from "./OperationsForm";

/** Bloque "Registrar una operación" de Cartera, sobre la cartera elegida en `?p=`. */
export function OperationsSection() {
  const [portfolioId] = usePortfolioId();
  return (
    <section aria-labelledby="operations-title" className="flex min-w-0 w-full flex-col gap-4">
      <div className="flex items-start gap-3">
        <span className="flex size-11 shrink-0 items-center justify-center rounded-control bg-icon-gold-bg text-icon-gold">
          <CoinsIcon className="size-6" />
        </span>
        <div className="flex min-w-0 flex-col gap-1">
          <h2 id="operations-title" className="m-0 text-xl font-semibold text-ink">
            Registrar una operación
          </h2>
          <p className="m-0 text-base text-ink-muted">
            Apunta aquí lo que ya has hecho en tu banco o bróker para que Kairos tenga la cartera al
            día. Solo se guarda en Kairos: no se envía ninguna orden a ningún sitio.
          </p>
        </div>
      </div>
      <OperationsForm key={portfolioId} portfolioId={portfolioId} />
    </section>
  );
}
