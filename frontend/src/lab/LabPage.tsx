/*
 * Laboratorio de componentes (T5-01). Solo existe con `npm run dev`: App.tsx monta la ruta
 * únicamente si `import.meta.env.DEV` y la carga con `lazy()`, así que no entra en el build.
 * No toca ninguna pantalla real; todos los datos son ilustrativos (ver mock.ts).
 */
import { Link } from "react-router";
import { ThemeToggle } from "../theme/ThemeToggle";
import { BandSection, SparklineSection } from "./ChartSections";
import { MetricSection, ProgressSection, SpotlightSection, UptimeSection } from "./CardSections";
import { GrainSection, RollingSection, StepsSection, TabsSection, TextMorphSection } from "./MotionSections";

export default function LabPage() {
  return (
    <main className="mx-auto grid max-w-4xl gap-6 px-4 py-8 lg:py-12">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="m-0 text-2xl font-semibold text-ink">Laboratorio de componentes</h1>
          <p className="m-0 mt-1 max-w-prose text-base text-ink-muted">
            Candidatos para la fase 5, con los tokens de KAIROS. Solo desarrollo. Todos los datos son
            ilustrativos (unidades abstractas «u.») y no vienen del motor de impacto. Cada componente
            lleva su veredicto frente a DESIGN.md.
          </p>
          <Link to="/inicio" className="mt-2 inline-block text-base text-accent underline underline-offset-2">
            Volver a la app
          </Link>
        </div>
        <ThemeToggle />
      </header>

      <BandSection />
      <SparklineSection />
      <MetricSection />
      <UptimeSection />
      <ProgressSection />
      <TabsSection />
      <StepsSection />
      <TextMorphSection />
      <RollingSection />
      <SpotlightSection />
      <GrainSection />
    </main>
  );
}
