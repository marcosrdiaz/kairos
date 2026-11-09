import { describe, expect, it } from "vitest";
import { buildPlan, emptyLine, weightToPercent, type PlanDraft } from "./planDraft";

const ref = (id: string) => ({ id, name: id, details: null });

function draft(percents: string[]): PlanDraft {
  return {
    amount: "300",
    frequency: "weekly",
    day: "3",
    lines: percents.map((p, i) => emptyLine(ref(`A${i}`), p)),
  };
}

describe("weightToPercent", () => {
  it.each([
    ["0.7", "70"],
    ["0.30", "30"],
    ["1", "100"],
    ["0.05", "5"],
    ["0.333333", "33,3333"],
  ])("%s -> %s", (weight, percent) => {
    expect(weightToPercent(weight)).toBe(percent);
  });
});

describe("buildPlan", () => {
  it("convierte porcentajes en fracciones exactas sin coma flotante", () => {
    const built = buildPlan(draft(["33,3333", "33,3333", "33,3334"]));
    expect(built.ok && built.body.allocations.map((a) => a.weight)).toEqual([
      "0.333333",
      "0.333333",
      "0.333334",
    ]);
    expect(built.ok && built.body.day).toBe(3);
  });

  it("0,1 + 0,2 + 99,7 suma 100 % exacto (donde un float fallaría)", () => {
    expect(buildPlan(draft(["0,1", "0,2", "99,7"])).ok).toBe(true);
  });

  it("si no suma 100 % lo dice con el total", () => {
    const built = buildPlan(draft(["50", "40,5"]));
    expect(built.ok).toBe(false);
    expect(!built.ok && built.errors.total).toBe("El reparto suma 90,5 % y tiene que sumar 100 %.");
  });

  it("marca activos repetidos y porcentajes vacíos o por encima de 100", () => {
    const d = draft(["", "120"]);
    d.lines.push(emptyLine(ref("A0"), "10"));
    const built = buildPlan(d);
    expect(!built.ok && built.errors.lines).toEqual([
      { percent: "Escribe una cifra." },
      { percent: "Como mucho 100 %." },
      { asset: "Este activo ya está en el reparto." },
    ]);
  });
});
