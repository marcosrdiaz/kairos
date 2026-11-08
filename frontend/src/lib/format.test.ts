import { describe, expect, it } from "vitest";
import { formatDate, formatEur, formatEurRange, formatPercent } from "./format";

// Intl usa U+00A0 antes de "€" y U+2212 como signo menos; normalizamos para comparar.
const n = (s: string) =>
  s.replaceAll(String.fromCharCode(160), " ").replaceAll(String.fromCharCode(0x2212), "-");

describe("format", () => {
  it("formatea euros desde string Decimal con coma decimal", () => {
    expect(n(formatEur("1234.5"))).toBe("1234,50 €");
  });
  it("redondea half-even solo al presentar", () => {
    expect(n(formatEur("2.5", 0))).toBe("2 €");
    expect(n(formatEur("3.5", 0))).toBe("4 €");
  });
  it("no pierde precisión con importes grandes", () => {
    expect(n(formatEur("123456789012345.67"))).toContain("123.456.789.012.345,67");
  });
  it("formatea rangos", () => {
    expect(n(formatEurRange("-640", "-380"))).toBe("entre -640 € y -380 €");
  });
  it("formatea porcentajes", () => {
    expect(n(formatPercent("0.0123"))).toBe("1,2 %");
  });
  it("formatea fechas en español", () => {
    expect(formatDate("2026-11-08T12:00:00Z")).toBe("8 de noviembre de 2026");
  });
});
