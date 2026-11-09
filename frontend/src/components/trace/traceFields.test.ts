import { describe, expect, it } from "vitest";
import { formatDate, formatEur, formatPercent } from "../../lib/format";
import { toTraceFields } from "./traceFields";

describe("toTraceFields", () => {
  it("da formato según la clave y nombra en español", () => {
    expect(toTraceFields({ total_eur: "34311.68", coverage_pct: "0.94", units: "114.00000000" })).toEqual([
      { key: "total_eur", label: "Valor total", text: formatEur("34311.68") },
      { key: "coverage_pct", label: "Cobertura", text: formatPercent("0.94") },
      { key: "units", label: "Participaciones", text: "114" },
    ]);
  });

  it("no pierde precisión con importes grandes", () => {
    const [field] = toTraceFields({ total_eur: "123456789012345.67" });
    expect(field).toMatchObject({ text: formatEur("123456789012345.67") });
    expect(field).toMatchObject({ text: expect.stringContaining("67") });
  });

  it("los hijos sin unidad heredan la del padre", () => {
    expect(toTraceFields({ value_eur: { IE00B4L5Y983: "10.50" } })).toEqual([
      {
        key: "value_eur",
        label: "Valor",
        fields: [{ key: "IE00B4L5Y983", label: "IE00B4L5Y983", text: formatEur("10.50") }],
      },
    ]);
  });

  it("nombra los elementos de una lista por su activo", () => {
    const [field] = toTraceFields({ positions: [{ asset_id: "NVDA", value_eur: "1.00" }] });
    expect(field).toMatchObject({
      label: "Posiciones",
      fields: [{ label: "NVDA", fields: [{ text: "NVDA" }, { text: formatEur("1.00") }] }],
    });
  });

  it("numera los elementos sin nombre", () => {
    const [field] = toTraceFields({ lots: [{ units: "1" }, { units: "2" }] });
    expect(field).toMatchObject({ fields: [{ label: "1" }, { label: "2" }] });
  });

  it("muestra nulos, vacíos, booleanos y fechas", () => {
    expect(toTraceFields({ a: null, b: [], c: {}, on_track: true, end: "2026-11-08T18:00:00Z" })).toEqual([
      { key: "a", label: "a", text: "—" },
      { key: "b", label: "b", text: "—" },
      { key: "c", label: "c", text: "—" },
      { key: "on_track", label: "En camino", text: "Sí" },
      { key: "end", label: "Fin", text: formatDate("2026-11-08T18:00:00Z") },
    ]);
  });

  it("un texto no numérico se queda igual aunque la clave tenga unidad", () => {
    expect(toTraceFields({ value_eur: "n/d" })).toMatchObject([{ text: "n/d" }]);
  });

  it("une las listas de valores simples", () => {
    expect(toTraceFields({ events: ["bce", "nvda"] })).toMatchObject([{ text: "bce, nvda" }]);
  });
});
