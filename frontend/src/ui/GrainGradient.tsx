/*
 * Fondo con degradado y grano, dibujado UNA vez con WebGL (sin animación ni bucle de
 * fotogramas). Adaptado de `grain-gradient.tsx` de Componentry
 * (https://github.com/harshjdhv/componentry, MIT): se conserva el shader, con el tiempo
 * fijo (el original con `speed=0`), y los colores salen de los tokens de KAIROS. Se vuelve a
 * dibujar al redimensionar y al cambiar de tema. Sin WebGL queda el degradado CSS de debajo.
 * Es decorativo: `aria-hidden`.
 */
import { useEffect, useRef } from "react";
import { cn } from "../lib/cn";

const VERTEX = `attribute vec2 a_position;
void main() { gl_Position = vec4(a_position, 0., 1.); }`;

const FRAGMENT = `precision highp float;
uniform vec2 u_resolution;
uniform float u_ratio, u_grain;
uniform vec3 u_light, u_mid, u_dark;
float hash(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * .1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}
void main() {
  vec2 uv = gl_FragCoord.xy / u_resolution;
  uv.y = 1. - uv.y;
  vec2 p = uv - .5;
  p.x *= u_resolution.x / u_resolution.y;
  p = p + .5;
  float edge = .32 + .48 * pow(1. - p.y, 2.) + .06;
  float distanceToEdge = p.x - edge + sin(p.y * 4. + .8) * .035;
  float diffusion = .16;
  float shadow = smoothstep(-diffusion, diffusion * .45, distanceToEdge);
  vec2 lightUV = (p - vec2(.1, .06)) * vec2(1.9, 1.7);
  float glow = exp(-dot(lightUV, lightUV));
  vec3 color = mix(u_light, u_mid, glow * .7);
  color = mix(color, u_mid * .97, smoothstep(-diffusion * 1.8, .02, distanceToEdge));
  color = mix(color, u_dark, shadow);
  float noise = hash(floor(gl_FragCoord.xy / u_ratio)) - .5;
  color += noise * u_grain * mix(.48, .32, shadow);
  gl_FragColor = vec4(clamp(color, 0., 1.), 1.);
}`;

function token(name: string): [number, number, number] {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const hex = /^#([\da-f]{6})$/i.exec(raw)?.[1] ?? "ffffff";
  return [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255) as [number, number, number];
}

function compile(gl: WebGLRenderingContext, type: number, source: string): WebGLShader | null {
  const shader = gl.createShader(type);
  if (!shader) return null;
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  return gl.getShaderParameter(shader, gl.COMPILE_STATUS) ? shader : null;
}

/** Prepara el contexto y devuelve la función que dibuja un fotograma, o null si no hay WebGL. */
function setup(canvas: HTMLCanvasElement, grain: number): (() => void) | null {
  const gl = canvas.getContext("webgl", { antialias: false });
  if (!gl) return null;
  const vertex = compile(gl, gl.VERTEX_SHADER, VERTEX);
  const fragment = compile(gl, gl.FRAGMENT_SHADER, FRAGMENT);
  const program = gl.createProgram();
  if (!vertex || !fragment || !program) return null;
  gl.attachShader(program, vertex);
  gl.attachShader(program, fragment);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return null;
  gl.useProgram(program);

  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const position = gl.getAttribLocation(program, "a_position");
  gl.enableVertexAttribArray(position);
  gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

  return () => {
    const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
    canvas.width = Math.max(1, Math.round(canvas.clientWidth * ratio));
    canvas.height = Math.max(1, Math.round(canvas.clientHeight * ratio));
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform2f(gl.getUniformLocation(program, "u_resolution"), canvas.width, canvas.height);
    gl.uniform1f(gl.getUniformLocation(program, "u_ratio"), ratio);
    gl.uniform1f(gl.getUniformLocation(program, "u_grain"), grain);
    gl.uniform3fv(gl.getUniformLocation(program, "u_light"), token("--kairos-color-surface"));
    gl.uniform3fv(gl.getUniformLocation(program, "u_mid"), token("--kairos-color-primary-tint"));
    gl.uniform3fv(gl.getUniformLocation(program, "u_dark"), token("--kairos-color-primary-tint-strong"));
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  };
}

export interface GrainGradientProps {
  /** Intensidad del grano, de 0 a 1. */
  grain?: number;
  className?: string;
}

export function GrainGradient({ grain = 0.22, className }: GrainGradientProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const draw = setup(canvas, grain);
    if (!draw) return;
    draw();
    const resize = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(draw);
    resize?.observe(canvas);
    const theme = new MutationObserver(draw);
    theme.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => {
      resize?.disconnect();
      theme.disconnect();
    };
  }, [grain]);

  return (
    <div
      aria-hidden="true"
      className={cn("relative overflow-hidden bg-gradient-to-br from-surface via-accent-tint to-accent-tint-strong", className)}
    >
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
    </div>
  );
}
