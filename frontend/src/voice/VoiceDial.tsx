/**
 * El visual del modo voz, con el lenguaje de la marca (oro → oro profundo):
 *
 * - En el centro, un disco dorado con la marca de KAIROS (las barras y la K) en blanco.
 * - Alrededor, una corona de barras, como las del logo, que se mueven con la voz: en reposo
 *   respiran despacio; escuchando, crecen con el volumen del micrófono; transcribiendo o
 *   pensando, un barrido da la vuelta; respondiendo, se mueven con la voz de la respuesta.
 * - Por fuera, órbitas finas y un punto que gira (como el globo de Inicio) y, al escuchar, ondas
 *   que salen del disco.
 *
 * El volumen se lee en cada fotograma (`getLevel`) y se escribe directamente en el SVG, sin
 * re-renderizar React. Con `prefers-reduced-motion`, todo queda quieto.
 */
import { useEffect, useId, useRef } from "react";

export type DialMode = "idle" | "listening" | "transcribing" | "thinking" | "speaking";

const BARS = 48;
const C = 130; // centro del viewBox
const R0 = 72; // radio donde nacen las barras
const ANGLES = Array.from({ length: BARS }, (_, i) => (i / BARS) * Math.PI * 2 - Math.PI / 2);

function prefersReducedMotion(): boolean {
  return typeof window.matchMedia === "function"
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : true;
}

function barLength(mode: DialMode, i: number, t: number, level: number): number {
  if (mode === "listening") {
    const wave = 0.5 + 0.5 * Math.sin(t * 6 + i * 0.9);
    const swell = 0.6 + 0.4 * Math.sin(t * 2.3 - i * 0.4);
    return 6 + 2 * Math.sin(t * 3 + i) + level * 44 * (0.35 + 0.65 * wave) * swell;
  }
  if (mode === "speaking") {
    // La voz de la respuesta: el volumen real si lo hay y, si no, un vaivén propio.
    const own = 0.35 + 0.25 * Math.sin(t * 7.1) * Math.sin(t * 2.9 + 1);
    const drive = Math.max(level, own);
    const wave = 0.5 + 0.5 * Math.sin(t * 5 - i * 0.55);
    return 6 + drive * 36 * (0.3 + 0.7 * wave);
  }
  if (mode === "transcribing" || mode === "thinking") {
    const head = (t * (mode === "thinking" ? 1.4 : 2.2)) % (Math.PI * 2);
    const d = Math.atan2(Math.sin((ANGLES[i] ?? 0) + Math.PI / 2 - head), Math.cos((ANGLES[i] ?? 0) + Math.PI / 2 - head));
    return 5 + 24 * Math.max(0, Math.cos(d)) ** 6;
  }
  return 5 + 4 * (0.5 + 0.5 * Math.sin(t * 1.2 + i * 0.35));
}

function endPoint(i: number, length: number): [number, number] {
  const a = (ANGLES[i] ?? 0);
  return [C + Math.cos(a) * (R0 + length), C + Math.sin(a) * (R0 + length)];
}

interface VoiceDialProps {
  mode: DialMode;
  getLevel: () => number;
  className?: string;
}

export function VoiceDial({ mode, getLevel, className = "size-60 sm:size-64" }: VoiceDialProps) {
  const id = `kairos-dial-${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const root = useRef<SVGSVGElement>(null);
  const bars = useRef<(SVGLineElement | null)[]>([]);

  useEffect(() => {
    const svg = root.current;
    if (!svg || prefersReducedMotion() || typeof requestAnimationFrame !== "function") return;
    let smooth = 0;
    let frame = requestAnimationFrame(function tick(now) {
      const t = now / 1000;
      const live = mode === "listening" || mode === "speaking";
      smooth += ((live ? getLevel() : 0) - smooth) * 0.2;
      svg.style.setProperty("--level", smooth.toFixed(3));
      bars.current.forEach((bar, i) => {
        if (!bar) return;
        const [x, y] = endPoint(i, barLength(mode, i, t, smooth));
        bar.setAttribute("x2", x.toFixed(1));
        bar.setAttribute("y2", y.toFixed(1));
      });
      frame = requestAnimationFrame(tick);
    });
    return () => {
      cancelAnimationFrame(frame);
      svg.style.setProperty("--level", "0");
    };
  }, [mode, getLevel]);

  return (
    <svg
      ref={root}
      viewBox="0 0 260 260"
      aria-hidden="true"
      focusable="false"
      className={`voice-dial is-${mode} ${className}`}
    >
      <defs>
        <linearGradient id={`${id}-gold`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="var(--kairos-color-gold)" />
          <stop offset="1" stopColor="var(--kairos-color-gold-deep)" />
        </linearGradient>
        <linearGradient id={`${id}-bars`} gradientUnits="userSpaceOnUse" x1="30" y1="30" x2="230" y2="230">
          <stop offset="0" stopColor="var(--kairos-color-gold)" />
          <stop offset="0.55" stopColor="var(--kairos-color-gold-deep)" />
          <stop offset="1" stopColor="var(--kairos-color-primary)" />
        </linearGradient>
        <radialGradient id={`${id}-glow`}>
          <stop offset="0.45" stopColor="var(--kairos-color-gold)" stopOpacity="0.35" />
          <stop offset="1" stopColor="var(--kairos-color-gold)" stopOpacity="0" />
        </radialGradient>
      </defs>

      <circle className="vd-glow" cx={C} cy={C} r="128" fill={`url(#${id}-glow)`} />

      {/* Órbitas: una discontinua con un punto que gira, otra fina y continua. */}
      <circle cx={C} cy={C} r="124" fill="none" stroke="var(--kairos-color-gold)" strokeOpacity="0.55" strokeWidth="1" strokeDasharray="2 7" strokeLinecap="round" />
      <circle cx={C} cy={C} r="112" fill="none" stroke="var(--kairos-color-gold-deep)" strokeOpacity="0.25" strokeWidth="1" />
      <g className="vd-orbit">
        <circle cx={C} cy={C - 124} r="4.5" fill="var(--kairos-color-gold)" />
      </g>
      <g className="vd-orbit vd-orbit-2">
        <circle cx={C} cy={C + 112} r="3" fill="var(--kairos-color-gold-deep)" />
      </g>

      {/* Ondas que salen del disco al escuchar. */}
      <circle className="vd-ripple" cx={C} cy={C} r="62" fill="none" stroke="var(--kairos-color-gold)" strokeWidth="1.5" />
      <circle className="vd-ripple vd-ripple-2" cx={C} cy={C} r="62" fill="none" stroke="var(--kairos-color-gold)" strokeWidth="1.5" />

      {/* Corona de barras. */}
      <g stroke={`url(#${id}-bars)`} strokeWidth="3.2" strokeLinecap="round">
        {ANGLES.map((a, i) => {
          const [x2, y2] = endPoint(i, 6);
          return (
            <line
              key={i}
              ref={(el) => {
                bars.current[i] = el;
              }}
              x1={(C + Math.cos(a) * R0).toFixed(1)}
              y1={(C + Math.sin(a) * R0).toFixed(1)}
              x2={x2.toFixed(1)}
              y2={y2.toFixed(1)}
            />
          );
        })}
      </g>

      {/* Disco con la marca. */}
      <g className="vd-core">
        <circle cx={C} cy={C} r="60" fill={`url(#${id}-gold)`} />
        <circle cx={C} cy={C} r="60" fill="none" stroke="var(--kairos-color-surface)" strokeOpacity="0.35" strokeWidth="1.5" />
        <ellipse cx={C - 18} cy={C - 26} rx="26" ry="14" fill="#fff" opacity="0.18" />
        <g transform={`translate(${C - 30} ${C - 23}) scale(0.94)`} fill="var(--kairos-color-surface)">
          <rect x="1" y="29" width="8" height="17" rx="1.5" />
          <rect x="12" y="20" width="8" height="26" rx="1.5" />
          <rect x="23" y="4" width="9" height="42" rx="1.5" />
          <path d="M32 27 50.5 4H62L37.5 32.5z" />
          <path d="M37 25.5 43.5 19 63 46H51.5z" />
        </g>
      </g>
    </svg>
  );
}
