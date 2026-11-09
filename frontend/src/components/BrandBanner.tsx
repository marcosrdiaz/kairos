import { LogoTile } from "./icons";

/** Ondas finas de fondo (decorativas), en oro con poca opacidad. */
function Waves() {
  return (
    <svg
      viewBox="0 0 300 140"
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
      className="pointer-events-none absolute inset-0 h-full w-full"
      fill="none"
      stroke="var(--kairos-color-gold)"
      strokeWidth="0.8"
    >
      {[0, 6, 12, 18, 24, 30, 36].map((d) => (
        <path
          key={d}
          d={`M-10 ${118 - d} C 60 ${70 - d}, 120 ${150 - d}, 190 ${86 - d} S 290 ${30 - d}, 320 ${54 - d}`}
          opacity={0.18 + d / 120}
        />
      ))}
    </svg>
  );
}

/**
 * Banner de marca de la barra lateral: logo, nombre y lema sobre un fondo crema (claro) o
 * negro cálido (oscuro) con ondas doradas. El lema va a 16 px (regla de DESIGN.md).
 */
export function BrandBanner() {
  return (
    <div className="relative isolate overflow-hidden bg-linear-to-br from-surface via-surface-muted to-accent-tint px-6 py-7">
      <Waves />
      <div className="relative flex items-center gap-3">
        <LogoTile className="size-14" />
        <span className="text-[2.125rem] font-semibold leading-none tracking-tight text-ink">
          Kairos
        </span>
      </div>
      <p className="relative m-0 mt-3 text-sm font-medium tracking-wide text-ink-muted">
        Analiza · comprende · decide
      </p>
    </div>
  );
}
