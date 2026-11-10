import { describe, expect, it } from "vitest";
import bce from "../../../api/mocks/EventImpactOut.json";
import nvda from "../../../api/mocks/EventImpactOut.nvda.json";
import type { EventImpactOut } from "../../../api/generated/schema";
import type { ChartRow } from "../chart/chartFormat";
import { markerLabel } from "../chart/markers/markerText";
import { placeAssetMarkers } from "./assetMarkers";

const BOND_FUND = "IE00B18GC888";
const NVDA = "US67066G1040";

const row = (date: string, value: number): ChartRow => ({
  date,
  value,
  raw: String(value),
  change: null,
  pct: null,
  flows: "0.00",
  hasFlow: false,
});

// Cierres en las fechas reales de los dos eventos de ejemplo.
const ROWS = [row("2025-02-26T00:00:00Z", 1000), row("2025-06-05T00:00:00Z", 1100)];
const EVENTS = [bce, nvda] as EventImpactOut[];

describe("placeAssetMarkers", () => {
  it("solo marca las noticias con impacto en ese activo, con su rango en la posición", () => {
    const markers = placeAssetMarkers(ROWS, EVENTS, BOND_FUND);
    const ids = markers.map((m) => m.event.event_id);
    expect(ids).toContain("bce-2025-06");
    const marker = markers.find((m) => m.event.event_id === "bce-2025-06");
    expect(marker?.position).toEqual({
      name: "Vanguard Global Bond Index Fund EUR Hedged Acc",
      low_eur: "5.00",
      high_eur: "117.00",
    });
  });

  it("no marca una noticia que no toca el activo", () => {
    const bceOnly = placeAssetMarkers(ROWS, [bce as EventImpactOut], NVDA);
    expect(bceOnly).toEqual([]);
  });

  it("no dibuja impactos sin rango por posición (guardados antes de T2-23)", () => {
    const old = structuredClone(bce) as EventImpactOut;
    old.breakdown = old.breakdown.map((b) => ({ ...b, low_eur: null, high_eur: null }));
    expect(placeAssetMarkers(ROWS, [old], BOND_FUND)).toEqual([]);
  });

  it("no marca un impacto de cero en esa posición", () => {
    const flat = structuredClone(bce) as EventImpactOut;
    flat.breakdown = flat.breakdown.map((b) => ({ ...b, impact_eur: "0.00" }));
    expect(placeAssetMarkers(ROWS, [flat], BOND_FUND)).toEqual([]);
  });

  it("el lector de pantalla oye el impacto en la posición, no en la cartera", () => {
    const [marker] = placeAssetMarkers(ROWS, [bce as EventImpactOut], BOND_FUND);
    expect(marker).toBeDefined();
    expect(markerLabel(marker!)).toMatch(
      /Impacto estimado en Vanguard Global Bond Index Fund EUR Hedged Acc entre 5\s€ y 117\s€, confianza media\.$/,
    );
  });
});
