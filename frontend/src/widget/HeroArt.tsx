/**
 * Ilustración de la cabecera de Inicio: "el mundo, traducido a tu cartera".
 * Un globo con una órbita de eventos que desemboca en una moneda en euros.
 * Decorativa (aria-hidden), sin ejes ni valores. Toma los colores de los tokens, así que
 * cambia sola con el modo; en oscuro añade estrellas y un halo más intenso.
 */
export function HeroArt({ className = "" }: { className?: string }) {
  const stroke = "var(--kairos-color-primary)";
  const gold = "var(--kairos-color-gold)";
  return (
    <svg
      viewBox="0 0 420 360"
      aria-hidden="true"
      focusable="false"
      className={className}
      preserveAspectRatio="xMaxYMid meet"
    >
      <defs>
        <radialGradient id="kairos-hero-glow" cx="0.55" cy="0.5" r="0.5">
          <stop offset="0" stopColor={gold} stopOpacity="0.45" className="dark:[stop-opacity:0.32]" />
          <stop offset="1" stopColor={gold} stopOpacity="0" />
        </radialGradient>
        <linearGradient id="kairos-hero-line" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={gold} />
          <stop offset="1" stopColor={stroke} />
        </linearGradient>
        <linearGradient id="kairos-hero-coin" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={gold} />
          <stop offset="1" stopColor={stroke} />
        </linearGradient>
      </defs>

      {/* Halo */}
      <circle cx="230" cy="180" r="175" fill="url(#kairos-hero-glow)" />

      {/* Estrellas: solo en modo oscuro */}
      <g fill={gold} className="opacity-0 dark:opacity-80">
        {[
          [40, 60, 1.6],
          [95, 300, 1.2],
          [150, 30, 1.4],
          [380, 40, 1.8],
          [400, 300, 1.3],
          [330, 340, 1.1],
          [60, 190, 1],
          [270, 20, 1.2],
        ].map(([x, y, r]) => (
          <circle key={`${x}-${y}`} cx={x} cy={y} r={r} />
        ))}
      </g>

      {/* Globo */}
      <g fill="none" stroke={stroke} strokeWidth="1.6" opacity="0.75">
        <circle cx="230" cy="180" r="110" />
        <ellipse cx="230" cy="180" rx="45" ry="110" />
        <ellipse cx="230" cy="180" rx="85" ry="110" />
        <path d="M120 180h220" />
        <path d="M135 125c50 14 140 14 190 0" />
        <path d="M135 235c50-14 140-14 190 0" />
      </g>

      {/* Órbita de eventos */}
      <ellipse
        cx="230"
        cy="180"
        rx="185"
        ry="62"
        fill="none"
        stroke="url(#kairos-hero-line)"
        strokeWidth="2"
        strokeDasharray="2 7"
        strokeLinecap="round"
        transform="rotate(-18 230 180)"
      />
      <g stroke={stroke} strokeWidth="2">
        {[
          [62, 236],
          [150, 116],
          [398, 126],
        ].map(([x, y]) => (
          <circle key={`${x}-${y}`} cx={x} cy={y} r="7" fill={gold} />
        ))}
      </g>

      {/* Del mundo a tu cartera: trazo hacia la moneda */}
      <path
        d="M150 116C210 150 260 230 318 262"
        fill="none"
        stroke="url(#kairos-hero-line)"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <g>
        <circle cx="338" cy="276" r="40" fill="url(#kairos-hero-coin)" />
        <circle
          cx="338"
          cy="276"
          r="31"
          fill="none"
          stroke="var(--kairos-color-surface)"
          strokeWidth="1.6"
          opacity="0.7"
        />
        <text
          x="338"
          y="290"
          textAnchor="middle"
          fontSize="38"
          fontWeight="700"
          fontFamily="var(--kairos-font)"
          fill="var(--kairos-color-surface)"
        >
          €
        </text>
      </g>
    </svg>
  );
}
