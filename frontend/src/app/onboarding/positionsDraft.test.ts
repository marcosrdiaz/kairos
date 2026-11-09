import { describe, expect, it } from "vitest";
import type { AssetOut } from "../../api/generated/schema";
import asset from "../../api/mocks/AssetOut.json";
import { buildPositions, emptyLine, todayInMadrid, type DraftLine } from "./positionsDraft";

const IWDA = asset as AssetOut;
const TODAY = "2026-11-09";

function line(patch: Partial<DraftLine>): DraftLine {
  return { ...emptyLine(), ...patch };
}

describe("buildPositions", () => {
  it("convierte las filas en PositionInitLine con strings Decimal", () => {
    const result = buildPositions(
      [
        line({ asset: IWDA, units: "114", cost: "80,27", date: "2023-03-06" }),
        line({ asset: IWDA, units: "1,5", cost: "92.2" }),
      ],
      TODAY,
    );
    expect(result).toEqual({
      ok: true,
      positions: [
        {
          asset_id: "IE00B4L5Y983",
          units: "114",
          avg_cost_eur: "80.27",
          acquired_at: "2023-03-06T00:00:00Z",
        },
        { asset_id: "IE00B4L5Y983", units: "1.5", avg_cost_eur: "92.2" },
      ],
    });
  });

  it("sin fecha no manda acquired_at (el backend usa hoy)", () => {
    const result = buildPositions([line({ asset: IWDA, units: "1", cost: "1" })], TODAY);
    expect(result.ok && "acquired_at" in result.positions[0]!).toBe(false);
  });

  it("devuelve un error por campo y fila, y los cuenta", () => {
    const result = buildPositions(
      [
        line({ asset: null, units: "", cost: "80,271" }),
        line({ asset: IWDA, units: "3", cost: "10", date: "2026-11-10" }),
      ],
      TODAY,
    );
    expect(result).toEqual({
      ok: false,
      count: 4,
      errors: [
        {
          asset: "Elige un activo de la lista.",
          units: "Escribe una cifra.",
          cost: "Como mucho 2 decimales (céntimos).",
        },
        { date: "La fecha de compra no puede ser futura." },
      ],
    });
  });

  it("la fecha de hoy vale", () => {
    expect(buildPositions([line({ asset: IWDA, units: "1", cost: "1", date: TODAY })], TODAY).ok).toBe(
      true,
    );
  });
});

describe("todayInMadrid", () => {
  it("usa la fecha de Madrid, no la UTC", () => {
    // 23:30 UTC del 9 de noviembre ya es día 10 en Madrid (UTC+1).
    expect(todayInMadrid(new Date("2026-11-09T23:30:00Z"))).toBe("2026-11-10");
  });
});
