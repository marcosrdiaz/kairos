import { MetricCard } from "../ui/MetricCard";
import { ProgressBar } from "../ui/ProgressBar";
import { SpotlightCard } from "../ui/SpotlightCard";
import { UptimeCard } from "../ui/UptimeCard";
import { LabSection } from "./LabSection";
import { METRIC_PERIODS, SOURCES, formatUnits } from "./mock";

export function MetricSection() {
  return (
    <LabSection
      id="metric"
      title="Tarjeta de cifra con periodos"
      origin="Kokonut UI · Metric Card · MIT"
      originUrl="https://kokonutui.com/docs/cards/metric-card"
      verdict={{
        fits: true,
        reason:
          "Usa los tokens de KAIROS; la variación lleva flecha, signo y palabra, y la bajada va en gris (trend-down), no en rojo. La cifra que rueda tiene su propio veredicto más abajo.",
      }}
      changes="colores de los tokens (el original es zinc), sin marcadores de eventos ni desglose, y la variación llega ya formateada: la tarjeta no calcula nada."
    >
      <MetricCard label="Cifra de ejemplo" periods={METRIC_PERIODS} formatValue={formatUnits} className="max-w-xl" />
    </LabSection>
  );
}

export function UptimeSection() {
  return (
    <LabSection
      id="uptime"
      title="Estado de las fuentes"
      origin="Kokonut UI · Uptime Card · MIT"
      originUrl="https://kokonutui.com/docs/cards/uptime-card"
      verdict={{
        fits: true,
        reason:
          "Tres estados siempre con palabra («Al día», «Con retraso», «Sin datos») y sin rojo: el original marca «caído» en rojo, y DESIGN.md lo reserva a errores del sistema. Barras planas, sin sombras.",
      }}
      changes="30 días en lugar de 90, sin la física de ensanchado ni el registro de incidencias, y la lectura del día en una línea de texto."
    >
      <UptimeCard title="Fuentes de datos (ejemplo)" sources={SOURCES} className="max-w-xl" />
    </LabSection>
  );
}

export function ProgressSection() {
  return (
    <LabSection
      id="progress"
      title="Barra de progreso frente a una regla"
      origin="Cult UI · Halo Progress · MIT"
      originUrl="https://www.cult-ui.com/docs/components/halo-progress"
      verdict={{
        fits: true,
        reason:
          "Sin sombras ni brillos: el original traía un resplandor multicolor, cristal esmerilado y sombras interiores, que chocaban con «sistema plano». Aquí queda un relleno de oro sobre un carril tonal, con la referencia del plan marcada.",
      }}
      changes="sin degradado ni cristal, sin barra indeterminada y sin la dependencia de Base UI; añade la marca de referencia (target)."
    >
      <div className="grid max-w-xl gap-6">
        <ProgressBar
          label="Aportaciones del plan (ejemplo)"
          value={3}
          max={4}
          valueText="3 de 4"
          target={4}
          targetLabel="La marca señala lo que prevé el plan."
        />
        <ProgressBar label="Objetivo de ejemplo" value={38} valueText="38 %" />
      </div>
    </LabSection>
  );
}

export function SpotlightSection() {
  return (
    <LabSection
      id="spotlight"
      title="Tarjeta con foco de luz"
      origin="Idea de React Bits · Spotlight Card (código propio)"
      originUrl="https://reactbits.dev/components/spotlight-card"
      verdict={{
        fits: false,
        reason:
          "El foco que sigue al ratón es decoración sin información. DESIGN.md pide capas tonales planas, sin destellos, y «nunca grita»; además solo existe con ratón, y la superficie principal es el móvil. Mejor no aplicarlo.",
      }}
      changes="no se copia código de React Bits (licencia MIT + Commons Clause): es una implementación propia de la misma idea. Solo con ratón y sin efecto con prefers-reduced-motion."
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <SpotlightCard>
          <p className="m-0 text-base font-medium text-ink">Tarjeta de ejemplo</p>
          <p className="m-0 mt-1 text-sm text-ink-muted">Pasa el ratón por encima para ver el foco.</p>
        </SpotlightCard>
        <SpotlightCard>
          <p className="m-0 text-base font-medium text-ink">Otra tarjeta</p>
          <p className="m-0 mt-1 text-sm text-ink-muted">En el móvil no se ve ningún efecto.</p>
        </SpotlightCard>
      </div>
    </LabSection>
  );
}
