/**
 * Fondo decorativo de la tarjeta de la gráfica, en la línea del asistente (`voice/ChatBackdrop`):
 * dos halos de luz dorados que derivan despacio y un haz de ondas finas en la parte baja.
 * Decorativo (aria-hidden) y con poca opacidad para no restar contraste. Sin movimiento con
 * `prefers-reduced-motion` (chart.css).
 */
function wave(y: number, amp: number, d: number): string {
  const a = amp + d * 0.5;
  return `M-20 ${y + d} C 120 ${y - a + d}, 260 ${y + a + d}, 400 ${y + d} S 680 ${y - a + d}, 820 ${y + d * 0.4}`;
}

export function ChartBackdrop() {
  return (
    <div aria-hidden="true">
      <div className="kchart-glow -right-24 -top-28 size-80 bg-(--kairos-color-gold) opacity-25" />
      <div className="kchart-glow -left-32 bottom-0 size-72 bg-(--kairos-color-chart-1) opacity-[0.12] [animation-delay:-8s]" />
      <svg className="kchart-waves" viewBox="0 0 800 200" preserveAspectRatio="none" fill="none" strokeWidth="0.8">
        <g stroke="var(--kairos-color-gold-deep)">
          {Array.from({ length: 6 }, (_, i) => (
            <path key={i} d={wave(120, 28, i * 8)} opacity={0.06 + i * 0.025} />
          ))}
        </g>
      </svg>
    </div>
  );
}
