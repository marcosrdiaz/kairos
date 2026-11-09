import { useId, type ReactNode, type SVGProps } from "react";

/**
 * Iconos en SVG en línea (sin librería: DESIGN.md). Son decorativos: aria-hidden y sin foco.
 * El significado siempre lo da el texto que los acompaña. Trazo con currentColor.
 */
type IconProps = Omit<SVGProps<SVGSVGElement>, "children">;

function Icon({ children, className = "size-6", ...rest }: IconProps & { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
      {...rest}
    >
      {children}
    </svg>
  );
}

/**
 * Marca: dos barras crecientes y una K cuyo trazo vertical es la tercera barra.
 * Degradado oro → oro profundo con tokens (cambia con el modo). Decorativa: el nombre va en texto.
 */
export function LogoMark({ className = "h-8 w-auto" }: IconProps) {
  // useId puede devolver ":r1:" o "«r1»": esos caracteres rompen url(#…) en fill.
  const id = `kairos-logo-${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  return (
    <svg viewBox="0 0 64 48" aria-hidden="true" focusable="false" className={className}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="var(--kairos-color-gold)" />
          <stop offset="1" stopColor="var(--kairos-color-gold-deep)" />
        </linearGradient>
      </defs>
      <g fill={`url(#${id})`}>
        <rect x="1" y="29" width="8" height="17" rx="1.5" />
        <rect x="12" y="20" width="8" height="26" rx="1.5" />
        <rect x="23" y="4" width="9" height="42" rx="1.5" />
        <path d="M32 27 50.5 4H62L37.5 32.5z" />
        <path d="M37 25.5 43.5 19 63 46H51.5z" />
      </g>
    </svg>
  );
}

/**
 * Logo en su cuadrado redondeado (como un icono de app), para que la K no se confunda con el
 * nombre que va al lado. Fondo papel: crema en claro y negro en oscuro.
 */
export function LogoTile({ className = "size-10" }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center rounded-[28%] border border-line bg-paper ${className}`}
    >
      <LogoMark className="block h-auto w-[70%]" />
    </span>
  );
}

export const HomeIcon =(p: IconProps) => (
  <Icon {...p}>
    <path d="M3 10.5 12 3l9 7.5" />
    <path d="M5 9.5V20h5v-6h4v6h5V9.5" />
  </Icon>
);

export const WalletIcon = (p: IconProps) => (
  <Icon {...p}>
    <rect x="3" y="6" width="18" height="14" rx="2.5" />
    <path d="M3 10h18" />
    <path d="M16 15h2" />
    <path d="M6 6V5a2 2 0 0 1 2-2h9" />
  </Icon>
);

export const ChatIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M4 5h16v11H9l-5 4z" />
    <path d="M8 9.5h8M8 12.5h5" />
  </Icon>
);

export const PanelIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M4 20V4" />
    <path d="M4 20h16" />
    <path d="M8 16v-4M12 16V8M16 16v-6" />
  </Icon>
);

export const SunIcon = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </Icon>
);

export const MoonIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" />
  </Icon>
);

export const ArrowRightIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Icon>
);

export const ArrowLeftIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M19 12H5M11 6l-6 6 6 6" />
  </Icon>
);

export const PauseIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M9 5v14M15 5v14" strokeWidth={2.4} />
  </Icon>
);

export const PlayIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M8 5l11 7-11 7z" />
  </Icon>
);

export const ArrowUpIcon =(p: IconProps) => (
  <Icon {...p}>
    <path d="M12 19V5M6 11l6-6 6 6" />
  </Icon>
);

export const ArrowDownIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M12 5v14M6 13l6 6 6-6" />
  </Icon>
);

export const CoinsIcon = (p: IconProps) => (
  <Icon {...p}>
    <ellipse cx="12" cy="6" rx="7" ry="3" />
    <path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6" />
    <path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
  </Icon>
);

export const TrendIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M3 17l6-6 4 4 8-8" />
    <path d="M15 7h6v6" />
  </Icon>
);

export const CompassIcon = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M15.5 8.5l-2 5-5 2 2-5z" />
  </Icon>
);

export const CalendarIcon = (p: IconProps) => (
  <Icon {...p}>
    <rect x="3" y="5" width="18" height="16" rx="2.5" />
    <path d="M3 10h18M8 3v4M16 3v4" />
  </Icon>
);
