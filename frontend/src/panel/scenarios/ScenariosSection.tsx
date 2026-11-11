import { useState, type CSSProperties } from "react";
import type { ScenarioOut } from "../../api/generated/schema";
import { useScenario } from "../../api/hooks/useScenario";
import { CONFIDENCE_LABEL } from "../../app/news/labels";
import { EmptyNote } from "../../components/PageTitle";
import { formatEur } from "../../lib/format";
import { impactRange, signedEur } from "../figures";
import { PanelSection } from "../PanelSection";
import { Traced } from "../Traced";
import { SCENARIO_PRESETS } from "./presets";

const TITLE = "¿Y si…?";
const INTRO =
  "Elige un supuesto y mira cómo afectaría a tu cartera hoy. Es una estimación para entender tu exposición, no una previsión ni una orden.";

/** Impacto por activo: el motor da una estimación puntual, así que va con «≈» y sin decimales. */
function approxEur(value: string): string {
  return Number(value) === 0 ? formatEur(value, 0) : `≈ ${signedEur(value, 0)}`;
}

type ScenarioAsset = ScenarioOut["breakdown"][number];

/** Valor absoluto de un importe en texto, sin pasarlo a number: solo se usa para dibujar. */
const absText = (value: string) => value.trim().replace(/^[+-]/, "");

/**
 * Impacto por activo como barras divergentes desde el cero (T5-16): a la izquierda lo que
 * restaría y a la derecha lo que sumaría, con la cifra al lado. El largo es solo dibujo (`calc`
 * frente al mayor impacto); el signo también va en el texto, no solo en el lado ni en el color.
 */
function ImpactBars({ assets, calcId }: { assets: ScenarioAsset[]; calcId: string }) {
  const max = absText(assets[0]?.impact_eur ?? "0");
  const hasMax = Number(max) !== 0;
  return (
    <>
      <p className="m-0 mt-6 text-sm text-ink-muted">
        Cada barra sale del cero: hacia la izquierda, lo que restaría a ese activo; hacia la
        derecha, lo que sumaría. El largo se compara con el mayor impacto.
      </p>
      <ul
        aria-label="Impacto estimado por activo"
        className="m-0 mt-4 flex list-none flex-col gap-4 p-0"
      >
        {assets.map((a) => {
          const loss = a.impact_eur.trim().startsWith("-");
          const width = hasMax ? `calc(${absText(a.impact_eur)} / ${max} * 50%)` : "0";
          return (
            <li key={a.asset_id} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1">
              <span className="text-base text-ink">
                {a.name}
                <span className="ml-2 text-sm text-ink-muted">hoy {formatEur(a.value_eur, 0)}</span>
              </span>
              <span className="text-right text-base font-semibold tabular-nums text-ink">
                <Traced calcId={calcId}>{approxEur(a.impact_eur)}</Traced>
              </span>
              <span
                aria-hidden="true"
                className="relative col-span-2 block h-2 rounded-full bg-surface-muted"
              >
                <span className="absolute inset-y-[-3px] left-1/2 w-px bg-line-strong" />
                <span
                  className={`absolute inset-y-0 rounded-full ${loss ? "right-1/2 bg-trend-loss" : "left-1/2 bg-trend-up"}`}
                  style={{ width } as CSSProperties}
                />
              </span>
            </li>
          );
        })}
      </ul>
    </>
  );
}

function ScenarioResult({ result }: { result: ScenarioOut }) {
  const assets = [...result.breakdown].sort(
    (a, b) => Math.abs(Number(b.impact_eur)) - Math.abs(Number(a.impact_eur)),
  );
  return (
    <div className="rounded-card border border-line bg-surface p-6">
      <dl className="m-0 flex flex-wrap items-end gap-x-8 gap-y-3">
        <div>
          <dt className="text-sm font-medium text-ink-muted">Impacto estimado en tu cartera</dt>
          <dd className="m-0 text-2xl font-semibold tabular-nums text-ink">
            <Traced calcId={result.calc_id}>{impactRange(result.low_eur, result.high_eur)}</Traced>
          </dd>
        </div>
        <div>
          <dt className="text-sm font-medium text-ink-muted">Fiabilidad</dt>
          <dd className="m-0 rounded-full bg-nodata-bg px-3 py-1 text-base font-semibold text-nodata">
            {CONFIDENCE_LABEL[result.confidence]}
          </dd>
        </div>
      </dl>

      {assets.length === 0 ? (
        <p className="m-0 mt-4 text-base text-ink-muted">
          Con los datos que tenemos, este supuesto no mueve ninguna de tus posiciones.
        </p>
      ) : (
        <ImpactBars assets={assets} calcId={result.calc_id} />
      )}
    </div>
  );
}

/** Escenarios ¿Y si…? (RF-21): el mismo motor que los eventos, con el supuesto que elige el usuario. */
export function ScenariosSection({ portfolioId }: { portfolioId: string }) {
  const [selected, setSelected] = useState<string | null>(null);
  const preset = SCENARIO_PRESETS.find((p) => p.id === selected) ?? null;
  const { data, isFetching, isError } = useScenario(portfolioId, selected, preset?.shocks ?? null);

  return (
    <PanelSection id="escenarios" title={TITLE} intro={INTRO} step={5}>
      <fieldset className="m-0 border-0 p-0">
        <legend className="mb-3 text-base font-semibold text-ink">Supuesto</legend>
        <div className="flex flex-wrap gap-2">
          {SCENARIO_PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              aria-pressed={p.id === selected}
              onClick={() => setSelected(p.id)}
              className="min-h-touch rounded-full border border-line bg-surface px-4 py-2 text-base font-medium text-ink transition-colors hover:border-accent aria-pressed:border-accent aria-pressed:bg-accent aria-pressed:text-on-accent"
            >
              {p.label}
            </button>
          ))}
        </div>
      </fieldset>

      <div aria-live="polite" className="mt-5">
        {preset && <p className="m-0 mb-3 text-base text-ink-muted">{preset.description}</p>}
        {!preset && (
          <EmptyNote>Elige un supuesto para ver cuánto podría moverse tu cartera.</EmptyNote>
        )}
        {preset && isFetching && !data && (
          <div
            role="status"
            aria-label="Calculando el escenario"
            className="h-32 rounded-card border border-line bg-surface-muted motion-safe:animate-pulse"
          />
        )}
        {preset && isError && !isFetching && (
          <EmptyNote>
            Ahora mismo no podemos calcular este escenario. Vuelve a intentarlo en unos segundos.
          </EmptyNote>
        )}
        {preset && data && <ScenarioResult result={data} />}
      </div>
    </PanelSection>
  );
}
