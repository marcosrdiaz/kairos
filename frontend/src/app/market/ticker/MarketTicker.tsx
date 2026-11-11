import { useState, type CSSProperties, type FocusEvent } from "react";
import { Link } from "react-router";
import { assetHref } from "../asset-chart/assetHref";
import type { TickerItemOut } from "../../../api/generated/schema";
import { useTicker } from "../../../api/hooks/useTicker";
import { PauseIcon, PlayIcon } from "../../../components/icons";
import { TraceFigure } from "../../../components/trace/TraceFigure";
import { signedPercent, trendOf } from "../../../widget/states";
import { issuerOf } from "./issuer";
import "./ticker.css";

/** Segundos que tarda cada activo en cruzar: con más activos, la vuelta dura más (misma velocidad). */
const SECONDS_PER_ITEM = 6;

/** Entradas mínimas por mitad del bucle, para que ninguna mitad sea más estrecha que la barra. */
const MIN_ENTRIES_PER_LOOP = 8;

const LOCALE = "es-ES";

const shortDate = new Intl.DateTimeFormat(LOCALE, {
  day: "numeric",
  month: "short",
  timeZone: "Europe/Madrid",
});

const priceFormatters = new Map<string, Intl.NumberFormat>();

/** Precio en la divisa del activo ("228.1", "USD" -> "228,10 US$"), sin pasar por float. */
function formatPrice(value: string, currency: string): string {
  let f = priceFormatters.get(currency);
  if (!f) {
    f = new Intl.NumberFormat(LOCALE, {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      roundingMode: "halfEven",
    });
    priceFormatters.set(currency, f);
  }
  return f.format(value as `${number}`);
}

function prefersReducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

const TREND = {
  up: { className: "text-trend-up", arrow: "▲", word: "sube" },
  down: { className: "text-trend-down", arrow: "▼", word: "baja" },
  flat: { className: "text-ink-muted", arrow: "■", word: "sin cambios" },
} as const;

/** Un activo: nombre corto, precio con su fecha y variación (con flecha y palabra, no solo color). */
function TickerEntry({ item, href }: { item: TickerItemOut & { change_pct: string }; href?: string }) {
  const trend = TREND[trendOf(item.change_pct)];
  const label = item.ticker ?? item.name;
  const issuer = issuerOf(item.name);
  return (
    <li className="flex shrink-0 items-baseline gap-2 px-5 text-sm whitespace-nowrap">
      <span aria-hidden="true" className="kairos-issuer-badge" data-issuer={issuer.key}>
        {issuer.initials}
      </span>
      {href ? (
        <Link
          to={href}
          className="font-semibold text-ink underline decoration-line-strong underline-offset-4 hover:text-accent hover:decoration-current"
          title={`${item.name}: ver su evolución`}
        >
          {label}
        </Link>
      ) : (
        <span className="font-semibold text-ink" title={item.name}>
          {label}
        </span>
      )}
      <span className="tabular-nums text-ink">{formatPrice(item.price, item.currency)}</span>
      <span className={`inline-flex items-baseline gap-1 tabular-nums ${trend.className}`}>
        <span aria-hidden="true" className="text-sm">
          {trend.arrow}
        </span>
        <span className="sr-only">{trend.word}</span>
        <TraceFigure calcId={item.calc_id}>{signedPercent(item.change_pct)}</TraceFigure>
      </span>
      <span className="text-sm text-ink-muted">
        <span className="sr-only">cierre del </span>
        <time dateTime={item.price_at}>{shortDate.format(new Date(item.price_at))}</time>
      </span>
    </li>
  );
}

const hasChange = (item: TickerItemOut): item is TickerItemOut & { change_pct: string } =>
  item.change_pct !== null && item.change_pct !== undefined;

interface TickerStripProps {
  items: TickerItemOut[];
  /** Enlace de cada activo a su evolución (T2-23). Sin él, el nombre no enlaza. */
  hrefFor?: (assetId: string) => string;
}

/**
 * Barra de cotizaciones que se desplaza sola (WCAG 2.2.2: pausar, detener, ocultar):
 * - Se detiene con el ratón encima, con el foco dentro y con el botón de pausa.
 * - Con `prefers-reduced-motion` no se mueve: la lista queda quieta y se puede desplazar a mano.
 * - Solo salen los activos con variación (los de precio fijo, como un depósito, no cotizan).
 * - Solo la primera lista se anuncia; las copias que llenan el bucle son `inert` y `aria-hidden`.
 */
export function TickerStrip({ items, hrefFor }: TickerStripProps) {
  const [reducedMotion] = useState(prefersReducedMotion);
  const [paused, setPaused] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);

  const quoted = items.filter(hasChange);
  if (quoted.length === 0) return null;

  const moving = !reducedMotion;
  const running = moving && !paused && !hovered && !focused;
  // Cada mitad del bucle debe ser más ancha que la barra: con pocos activos se repiten.
  const repeats = Math.ceil(MIN_ENTRIES_PER_LOOP / quoted.length);
  const duration = `${repeats * quoted.length * SECONDS_PER_ITEM}s`;
  const style = { "--ticker-duration": duration } as CSSProperties;

  const onBlur = (e: FocusEvent<HTMLElement>) => {
    if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setFocused(false);
  };

  const list = (copy: boolean, key?: number) => (
    <ul
      key={key}
      className="m-0 flex shrink-0 list-none p-0"
      aria-hidden={copy || undefined}
      inert={copy || undefined}
    >
      {quoted.map((item) => (
        <TickerEntry key={item.asset_id} item={item} href={hrefFor?.(item.asset_id)} />
      ))}
    </ul>
  );
  /** Copias ocultas: las que completan la primera mitad y la segunda mitad entera. */
  const copies = (count: number, from: number) =>
    Array.from({ length: count }, (_, i) => list(true, from + i));

  return (
    <section
      aria-labelledby="ticker-heading"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setFocused(true)}
      onBlur={onBlur}
      className="flex min-h-15 items-center gap-3 rounded-card border border-line bg-surface py-2 pr-2 pl-4"
    >
      <h2 id="ticker-heading" className="m-0 shrink-0 text-sm font-semibold text-ink-muted">
        Tus activos
      </h2>
      <div
        className={`min-w-0 flex-1 ${moving ? "kairos-ticker-viewport overflow-hidden" : "overflow-x-auto"}`}
        aria-live="off"
      >
        <div
          className={`flex w-max ${moving ? "kairos-ticker-track" : ""}`}
          data-state={running ? "running" : "paused"}
          style={moving ? style : undefined}
        >
          {list(false)}
          {moving && copies(2 * repeats - 1, 1)}
        </div>
      </div>
      {moving && (
        <button
          type="button"
          onClick={() => setPaused((p) => !p)}
          className="inline-flex size-11 shrink-0 items-center justify-center rounded-full border border-line-strong bg-surface text-ink hover:bg-surface-muted"
          aria-label={paused ? "Reanudar el desplazamiento de precios" : "Pausar el desplazamiento de precios"}
        >
          {paused ? <PlayIcon className="size-5" /> : <PauseIcon className="size-5" />}
        </button>
      )}
    </section>
  );
}

/**
 * Ticker de Inicio (T2-17): carga los precios de la cartera y, si no hay, no ocupa sitio. Una
 * respuesta sin lista (error, backend falso de otro test) tampoco debe romper la página.
 */
export function MarketTicker({ portfolioId }: { portfolioId: string }) {
  const { data } = useTicker(portfolioId);
  if (!data || !Array.isArray(data.items)) return null;
  return <TickerStrip items={data.items} hrefFor={(assetId) => assetHref(assetId, portfolioId)} />;
}
