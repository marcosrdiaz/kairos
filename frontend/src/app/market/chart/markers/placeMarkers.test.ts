import { describe, expect, it } from "vitest";
import bce from "../../../../api/mocks/EventImpactOut.json";
import nvda from "../../../../api/mocks/EventImpactOut.nvda.json";
import type { EventImpactOut } from "../../../../api/generated/schema";
import type { ChartRow } from "../chartFormat";
import { markersByDate, placeMarkers, stackLevels } from "./placeMarkers";

const row = (date: string, value: number): ChartRow => ({
  date: `${date}T00:00:00Z`,
  value,
  raw: value.toFixed(2),
  change: null,
  pct: null,
  flows: "0.00",
  hasFlow: false,
});

const BCE = bce as EventImpactOut; // market_date 2025-06-05
const NVDA = nvda as EventImpactOut; // market_date 2025-02-26

describe("placeMarkers", () => {
  it("coloca el evento en el cierre de su fecha real, no en la del replay", () => {
    const rows = [row("2025-06-04", 100), row("2025-06-05", 101), row("2025-06-06", 102)];
    const [marker] = placeMarkers(rows, [BCE]);
    expect(marker?.date).toBe("2025-06-05T00:00:00Z");
    expect(marker?.value).toBe(101);
    expect(BCE.occurred_at.startsWith("2026")).toBe(true); // la del replay queda fuera
  });

  it("con puntos semanales usa el cierre más cercano", () => {
    const rows = [row("2025-05-30", 100), row("2025-06-06", 102), row("2025-06-13", 103)];
    expect(placeMarkers(rows, [BCE])[0]?.date).toBe("2025-06-06T00:00:00Z");
  });

  it("fuera del periodo o sin fecha real, no se dibuja", () => {
    const rows = [row("2025-11-06", 100), row("2026-11-06", 120)];
    expect(placeMarkers(rows, [BCE, NVDA])).toEqual([]);
    const old = { ...BCE, market_date: null } as EventImpactOut;
    expect(placeMarkers([row("2025-06-05", 1)], [old])).toEqual([]);
  });

  it("apila las noticias cercanas para que no se pisen", () => {
    // Serie semanal de 30 viernes desde el 30 de mayo de 2025 (como la de «Todo»).
    const rows = Array.from({ length: 30 }, (_, i) =>
      row(new Date(Date.UTC(2025, 4, 30 + i * 7)).toISOString().slice(0, 10), i),
    );
    const oil = { ...BCE, event_id: "oil", market_date: "2025-06-13T01:42:00Z" } as EventImpactOut;
    const late = { ...BCE, event_id: "late", market_date: "2025-12-12T00:00:00Z" } as EventImpactOut;
    const markers = placeMarkers(rows, [BCE, oil, late]);
    // 6 px entre puntos: BCE y petróleo (un punto de distancia) se apilan; el de diciembre, no.
    expect(Object.fromEntries(stackLevels(markers, rows, 6))).toEqual({ "bce-2025-06": 0, oil: 1, late: 0 });
    expect(Object.fromEntries(stackLevels(markers, rows, 60))).toEqual({ "bce-2025-06": 0, oil: 0, late: 0 });
  });

  it("ordena por fecha real y agrupa por cierre para la tabla", () => {
    const rows = [row("2025-02-26", 90), row("2025-06-05", 101)];
    const markers = placeMarkers(rows, [BCE, NVDA]);
    expect(markers.map((m) => m.event.event_id)).toEqual(["nvda-2025-02", "bce-2025-06"]);
    expect(markersByDate(markers).get("2025-06-05T00:00:00Z")?.[0]?.event.event_id).toBe("bce-2025-06");
  });
});
