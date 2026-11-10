import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

// Vitest corre desde frontend/ (npm test, make test). Con jsdom, import.meta.url no es file:.
const css = readFileSync(resolve(process.cwd(), "src/styles/tokens.css"), "utf8");

/**
 * Contraste WCAG 2.2 de los tokens de color en modo claro y oscuro.
 * Texto: ≥ 4,5:1 (AA, 1.4.3). Bordes de control, foco y marcas de gráfico: ≥ 3:1 (AA, 1.4.11).
 */
function block(selector: string): Record<string, string> {
  const start = css.indexOf(`${selector} {`);
  if (start < 0) throw new Error(`No encuentro ${selector}`);
  const body = css.slice(start, css.indexOf("}", start));
  const out: Record<string, string> = {};
  for (const m of body.matchAll(/--kairos-color-([\w-]+):\s*(#[0-9a-fA-F]{6})/g)) {
    out[m[1]!] = m[2]!;
  }
  return out;
}

const light = block(":root");
// El oscuro hereda del claro lo que no redefine.
const dark = { ...light, ...block('[data-theme="dark"]') };

function luminance(hex: string): number {
  const ch = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const [r, g, b] = ch.map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)) as [
    number,
    number,
    number,
  ];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
}

/** [primer plano, fondo] */
const TEXT_PAIRS: [string, string][] = [
  ["text", "bg"],
  ["text", "surface"],
  ["text", "surface-muted"],
  ["text", "primary-tint"],
  ["text-muted", "bg"],
  ["text-muted", "surface"],
  ["text-muted", "surface-muted"],
  ["text-muted", "primary-tint"],
  ["primary", "bg"],
  ["primary", "surface"],
  ["primary", "surface-muted"],
  ["primary", "primary-tint"],
  ["on-primary", "primary"],
  ["on-primary", "primary-hover"],
  ["state-tranquilo-fg", "state-tranquilo-bg"],
  ["state-atento-fg", "state-atento-bg"],
  ["state-revisa-plan-fg", "state-revisa-plan-bg"],
  ["chip-success-fg", "chip-success-bg"],
  ["chip-warn-fg", "chip-warn-bg"],
  ["chip-error-fg", "chip-error-bg"],
  ["chip-info-fg", "chip-info-bg"],
  ["chip-nodata-fg", "chip-nodata-bg"],
  ["trend-up", "surface"],
  ["trend-down", "surface"],
  ["trend-loss", "surface"],
  ["trend-loss", "trend-loss-bg"],
];

const UI_PAIRS: [string, string][] = [
  ["border-strong", "bg"],
  ["border-strong", "surface"],
  ["focus", "bg"],
  ["focus", "surface"],
  ["icon-gold-fg", "icon-gold-bg"],
  ["icon-green-fg", "icon-green-bg"],
  ["icon-purple-fg", "icon-purple-bg"],
  ["icon-blue-fg", "icon-blue-bg"],
  ["icon-red-fg", "icon-red-bg"],
  ["state-tranquilo-solid", "surface"],
  ["state-atento-solid", "surface"],
  ["state-revisa-plan-solid", "surface"],
  ["chart-1", "surface"],
  ["chart-2", "surface"],
  ["chart-3", "surface"],
  ["chart-4", "surface"],
];

describe.each([
  ["claro", light],
  ["oscuro", dark],
])("contraste en modo %s", (_name, tokens) => {
  const get = (k: string) => {
    const v = tokens[k];
    if (!v) throw new Error(`Falta --kairos-color-${k}`);
    return v;
  };
  it.each(TEXT_PAIRS)("texto %s sobre %s ≥ 4,5:1", (fg, bg) => {
    expect(contrast(get(fg), get(bg))).toBeGreaterThanOrEqual(4.5);
  });
  it.each(UI_PAIRS)("elemento %s sobre %s ≥ 3:1", (fg, bg) => {
    expect(contrast(get(fg), get(bg))).toBeGreaterThanOrEqual(3);
  });
});

describe("tokens", () => {
  it("el modo oscuro redefine los mismos colores que el claro", () => {
    expect(Object.keys(block('[data-theme="dark"]')).sort()).toEqual(Object.keys(light).sort());
  });
});
