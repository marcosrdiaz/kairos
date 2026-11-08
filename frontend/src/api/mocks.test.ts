import { describe, expect, it } from "vitest";
import { getMock } from "./client";
import type { PortfolioOut } from "./generated/schema";

// `make gen-api` (T0-03) copia aquí los ejemplos del backend. Estos tests comprueban que el
// frontend los importa con los tipos generados; no fijan cifras (son ilustrativas).
const mockFiles = Object.keys(import.meta.glob("./mocks/*.json"));

describe("mocks generados", () => {
  it("hay mocks copiados desde backend/app/schemas/examples", () => {
    expect(mockFiles.length).toBeGreaterThan(0);
  });

  it("todos siguen el patrón <Modelo>.json o <Modelo>.<variante>.json", () => {
    for (const file of mockFiles) {
      expect(file).toMatch(/^\.\/mocks\/[A-Z][A-Za-z]+(\.[a-z0-9_]+)?\.json$/);
    }
  });

  it("getMock devuelve la cartera de ejemplo tipada con el esquema generado", () => {
    const laura = getMock<PortfolioOut>("PortfolioOut");
    expect(laura?.id).toBe("laura");
    expect(typeof laura?.total_eur).toBe("string");
    expect(Array.isArray(laura?.positions)).toBe(true);
  });

  it("getMock sirve también las variantes", () => {
    expect(getMock<PortfolioOut>("PortfolioOut.javier")?.id).toBe("javier");
  });
});
