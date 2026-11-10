import { useState } from "react";
import { RangeBandChart } from "../ui/RangeBandChart";
import { Sparkline } from "../ui/Sparkline";
import { describeSeries } from "../ui/sparkline-geometry";
import { BAND_DATA, BAND_SPLIT, SPARKLINES, bandLabel, formatUnits } from "./mock";
import { LabSection } from "./LabSection";

export function BandSection() {
  return (
    <LabSection
      id="band"
      title="Línea con banda de rango"
      origin="Bklit UI · Band · MIT"
      originUrl="https://bklit.com/docs/components/line-chart"
      verdict={{
        fits: true,
        reason:
          "Es plano y sin sombras: la banda es un tinte de chart-1 sobre la superficie y no usa rojo. Cumple la regla de producto 5: lo estimado se enseña como rango (low–high) alrededor de una línea central discontinua.",
      }}
      changes="sin animación de entrada ni morphing, lectura en una línea de texto (no en una ventana flotante), tabla accesible y teclado con flechas."
    >
      <RangeBandChart
        data={BAND_DATA}
        splitIndex={BAND_SPLIT}
        formatX={bandLabel}
        formatValue={formatUnits}
        label="Serie ilustrativa: 6 meses observados y 4 estimados con rango"
      />
    </LabSection>
  );
}

export function SparklineSection() {
  const [hover, setHover] = useState<Record<string, number | null>>({});
  return (
    <LabSection
      id="sparkline"
      title="Sparklines"
      origin="Bklit UI · Sparkline · MIT"
      originUrl="https://bklit.com/docs/components/sparkline"
      verdict={{
        fits: true,
        reason:
          "Planos, sin ejes ni sombras. El color nunca es la única señal: cada uno lleva su resumen en texto («sube un 35 %») para el lector de pantalla y el valor exacto al pasar el cursor.",
      }}
      changes="solo línea y área (se quitan las barras), geometría adaptada, resumen en español y sin animación."
    >
      <table className="w-full border-collapse text-left">
        <caption className="sr-only">Series ilustrativas con su sparkline</caption>
        <thead className="text-sm text-ink-muted">
          <tr>
            <th scope="col" className="py-2 pr-3 font-medium">Serie</th>
            <th scope="col" className="py-2 pr-3 font-medium">Evolución</th>
            <th scope="col" className="py-2 font-medium">Valor</th>
          </tr>
        </thead>
        <tbody>
          {SPARKLINES.map(({ name, values }) => {
            const index = hover[name];
            return (
              <tr key={name} className="border-t border-line">
                <th scope="row" className="py-3 pr-3 text-base font-medium text-ink">
                  {name}
                  <span className="block text-sm font-normal text-ink-muted">{describeSeries(values, formatUnits)}</span>
                </th>
                <td className="py-3 pr-3">
                  <Sparkline
                    values={values}
                    width={140}
                    height={36}
                    formatValue={formatUnits}
                    onActiveChange={(i) => setHover((h) => ({ ...h, [name]: i }))}
                  />
                </td>
                <td className="py-3 text-base tabular-nums text-ink">
                  {index === null || index === undefined ? "—" : formatUnits(values[index] ?? 0)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </LabSection>
  );
}
