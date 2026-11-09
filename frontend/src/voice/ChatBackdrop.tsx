/**
 * Fondo del asistente (panel en escritorio, modal en móvil). Parte de la idea del banner de
 * marca (ondas finas sobre un degradado cálido), pero con más variedad: manchas de luz en los
 * cuatro colores de gráfica (oro, verde azulado, violeta y azul) y tres haces de ondas, cada uno
 * en un color, que derivan despacio. Decorativo y con poca opacidad para no restar contraste al
 * texto (las burbujas llevan su propio fondo). Sin movimiento con `prefers-reduced-motion`.
 */

const BANDS = [
  { color: "var(--kairos-color-chart-1)", y: 70, amp: 34, lines: 6, cls: "chat-wave-a" },
  { color: "var(--kairos-color-chart-2)", y: 300, amp: 26, lines: 5, cls: "chat-wave-b" },
  { color: "var(--kairos-color-chart-3)", y: 520, amp: 40, lines: 6, cls: "chat-wave-c" },
] as const;

function wave(y: number, amp: number, d: number): string {
  const a = amp + d * 0.6;
  return `M-40 ${y + d} C 60 ${y - a + d}, 140 ${y + a + d}, 220 ${y + d} S 380 ${y - a + d}, 460 ${y + d * 0.5}`;
}

export function ChatBackdrop() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10 overflow-hidden bg-paper">
      <div className="chat-glow absolute -right-24 -top-24 size-80 rounded-full bg-(--kairos-color-chart-1) opacity-[0.16] blur-3xl" />
      <div className="chat-glow absolute -left-28 top-1/3 size-72 rounded-full bg-(--kairos-color-chart-3) opacity-[0.12] blur-3xl [animation-delay:-6s]" />
      <div className="chat-glow absolute -bottom-24 left-1/4 size-80 rounded-full bg-(--kairos-color-chart-2) opacity-[0.12] blur-3xl [animation-delay:-12s]" />
      <div className="chat-glow absolute -bottom-16 -right-16 size-56 rounded-full bg-(--kairos-color-chart-4) opacity-[0.10] blur-3xl [animation-delay:-3s]" />
      <svg
        viewBox="0 0 420 640"
        preserveAspectRatio="xMidYMid slice"
        className="absolute inset-0 h-full w-full"
        fill="none"
        strokeWidth="0.9"
      >
        {BANDS.map((band) => (
          <g key={band.y} stroke={band.color} className={band.cls}>
            {Array.from({ length: band.lines }, (_, i) => (
              <path key={i} d={wave(band.y, band.amp, i * 7)} opacity={0.1 + i * 0.035} />
            ))}
          </g>
        ))}
      </svg>
    </div>
  );
}
