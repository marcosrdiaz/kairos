import { useState } from "react";
import { buttonSecondary } from "../components/button";
import { GrainGradient } from "../ui/GrainGradient";
import { PipelineSteps } from "../ui/PipelineSteps";
import { RollingNumber } from "../ui/RollingNumber";
import { SwipeTabs } from "../ui/SwipeTabs";
import { TextMorph } from "../ui/TextMorph";
import { LabSection } from "./LabSection";
import { HEADLINES, PIPELINE, formatUnits } from "./mock";

const VALUES = [1234, 5678, 2468];

export function RollingSection() {
  const [step, setStep] = useState(0);
  return (
    <LabSection
      id="rolling"
      title="Número que rueda"
      origin="Cult UI · Rolling Number · MIT"
      originUrl="https://www.cult-ui.com/docs/components/rolling-number"
      verdict={{
        fits: false,
        reason:
          "«Calma, nunca alarma»: las cifras que ruedan recuerdan a una cotización en directo y empujan a mirar el dinero minuto a minuto. Solo lo aceptaría una vez al cargar o cambiar de cartera, y la cifra seguiría envuelta en Traced. Aquí rueda solo cuando pulsas el botón.",
      }}
      changes="muelle sobreamortiguado (sin rebote), salto directo con prefers-reduced-motion y valor final siempre disponible para lectores de pantalla."
    >
      <div className="flex flex-wrap items-center gap-6">
        <p className="m-0 text-hero leading-tight font-semibold text-ink">
          <RollingNumber value={VALUES[step % VALUES.length] ?? 0} format={formatUnits} />
        </p>
        <button type="button" className={buttonSecondary} onClick={() => setStep((s) => s + 1)}>
          Cambiar el valor
        </button>
      </div>
    </LabSection>
  );
}

export function TextMorphSection() {
  const [step, setStep] = useState(0);
  return (
    <LabSection
      id="morph"
      title="Cambio suave de frase"
      origin="Componentry · Text Morph · MIT"
      originUrl="https://componentry.dev/docs/components/text-morph"
      verdict={{
        fits: true,
        reason:
          "Solo cambia cuando cambia el texto (no rota solo) y dura 0,3 s con un desenfoque ligero: apto para la frase de estado de Inicio. Con prefers-reduced-motion el cambio es instantáneo.",
      }}
      changes="se quita la rotación automática y el filtro SVG de umbral; el texto nuevo se anuncia al lector de pantalla."
    >
      <div className="flex flex-wrap items-center gap-6">
        <p className="m-0 min-w-72 text-2xl font-semibold text-ink">
          <TextMorph text={HEADLINES[step % HEADLINES.length] ?? ""} />
        </p>
        <button type="button" className={buttonSecondary} onClick={() => setStep((s) => s + 1)}>
          Cambiar la frase
        </button>
      </div>
    </LabSection>
  );
}

export function TabsSection() {
  return (
    <LabSection
      id="tabs"
      title="Pestañas con indicador deslizante"
      origin="Kokonut UI · Swipe Tabs · MIT"
      originUrl="https://kokonutui.com/docs/navigation/smooth-tab"
      verdict={{
        fits: true,
        reason:
          "Mismo lenguaje que la navegación de DESIGN.md: píldora de oro con texto on-primary, 44 px de alto, estado activo por forma y color, y teclado completo (flechas, Inicio y Fin).",
      }}
      changes="el indicador usa layoutId de motion, el gesto se reduce a deslizar con umbral y se quitan los iconos de lucide."
    >
      <SwipeTabs
        label="Secciones de ejemplo"
        items={[
          { id: "a", title: "Resumen", content: <p className="m-0 text-base text-ink">Contenido de ejemplo del resumen.</p> },
          { id: "b", title: "Eventos", content: <p className="m-0 text-base text-ink">Contenido de ejemplo de los eventos.</p> },
          { id: "c", title: "Trazas", content: <p className="m-0 text-base text-ink">Contenido de ejemplo de las trazas.</p> },
        ]}
      />
      <p className="m-0 mt-3 text-sm text-ink-muted">En el móvil también se cambia deslizando el panel.</p>
    </LabSection>
  );
}

export function StepsSection() {
  const [current, setCurrent] = useState(1);
  return (
    <LabSection
      id="steps"
      title="Pasos de un proceso"
      origin="Kokonut UI · Currency Transfer · MIT"
      originUrl="https://kokonutui.com/docs/cards/currency-transfer"
      verdict={{
        fits: true,
        reason:
          "Cada paso lleva marcador y palabra («Hecho», «En curso», «Pendiente»): nunca solo color. No avanza solo; lo controla quien lo usa.",
      }}
      changes="solo la línea de pasos (sin importes, bancos ni referencia copiable), controlada y sin autoplay."
    >
      <PipelineSteps steps={PIPELINE} current={current} label="Pasos de ejemplo" />
      <div className="mt-4 flex gap-3">
        <button
          type="button"
          className={buttonSecondary}
          disabled={current >= PIPELINE.length}
          onClick={() => setCurrent((c) => Math.min(PIPELINE.length, c + 1))}
        >
          Siguiente paso
        </button>
        <button type="button" className={buttonSecondary} onClick={() => setCurrent(0)}>
          Reiniciar
        </button>
      </div>
    </LabSection>
  );
}

export function GrainSection() {
  return (
    <LabSection
      id="grain"
      title="Fondo con grano"
      origin="Componentry · Grain Gradient · MIT"
      originUrl="https://componentry.dev/docs/components/grain-gradient"
      verdict={{
        fits: false,
        reason:
          "DESIGN.md pide capas tonales planas y bordes finos. El grano y el borde difuso son ruido visual sobre una cabecera que ya tiene degradado de tinte y la ilustración HeroArt, y añaden un contexto WebGL por cabecera. Mejor no aplicarlo.",
      }}
      changes="se dibuja una sola vez (sin animación ni bucle), con los colores de los tokens y redibujo al cambiar de tema; sin WebGL queda el degradado CSS."
    >
      <GrainGradient className="h-44 rounded-card border border-line" />
    </LabSection>
  );
}
