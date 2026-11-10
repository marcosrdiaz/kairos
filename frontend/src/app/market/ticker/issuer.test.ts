import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { issuerOf } from "./issuer";

const css = readFileSync(resolve(process.cwd(), "src/app/market/ticker/ticker.css"), "utf8");

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
const contrast = (a: string, b: string) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
};

const RULE = String.raw`\.kairos-issuer-badge\[data-issuer="(\w+)"\] \{\s*--issuer-bg: (#[0-9a-f]{6});\s*--issuer-fg: (#[0-9a-f]{6});`;
const DARK = String.raw`\[data-theme="dark"\] `;

/** Pares [emisor, fondo, texto] leídos de ticker.css, por modo. */
function pairs(dark: boolean): [string, string, string][] {
  const re = new RegExp(`^${dark ? DARK : ""}${RULE}`, "gm");
  return [...css.matchAll(re)].map((m) => [m[1]!, m[2]!, m[3]!]);
}

describe("colores de emisor", () => {
  it.each([false, true])("hay un color por grupo conocido y pasa AA (oscuro: %s)", (dark) => {
    const found = pairs(dark);
    expect(found.map((f) => f[0]).sort()).toEqual(
      ["apple", "iberdrola", "inditex", "ishares", "microsoft", "nvidia", "vanguard"].sort(),
    );
    for (const [key, bg, fg] of found) {
      expect(contrast(fg, bg), `${key} ${dark ? "oscuro" : "claro"}`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("no usa tonos de estado ni de chip (el color se reserva para los estados)", () => {
    const rules = css.slice(css.indexOf(".kairos-issuer-badge {"));
    const declarations = rules.replace(/\/\*[\s\S]*?\*\//g, "");
    expect(declarations).not.toMatch(/state-|chip-(success|warn|error|info)|icon-|primary|trend-/);
  });

  it("solo iniciales: las conocidas son de dos letras y la desconocida, una", () => {
    expect(issuerOf("Vanguard Global").initials).toHaveLength(2);
    expect(issuerOf("Algo raro").initials).toBe("A");
  });
});
