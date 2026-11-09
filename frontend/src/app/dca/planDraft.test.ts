import { describe, expect, it } from "vitest";
import {
  buildPlan,
  carryLineErrors,
  DUPLICATE_ASSET,
  emptyLine,
  weightToPercent,
  type PlanDraft,
} from "./planDraft";

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
    ["0.33333333", "33,333333"],
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

  it("acepta los 8 decimales de peso que guarda la BD (6 de porcentaje)", () => {
    const built = buildPlan(draft(["33,333333", "33,333333", "33,333334"]));
    expect(built.ok && built.body.allocations.map((a) => a.weight)).toEqual([
      "0.33333333",
      "0.33333333",
      "0.33333334",
    ]);
  });

  it("33,33 × 3 no llega a 100 %", () => {
    const built = buildPlan(draft(["33,33", "33,33", "33,33"]));
    expect(!built.ok && built.errors.total).toBe("El reparto suma 99,99 % y tiene que sumar 100 %.");
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

describe("carryLineErrors", () => {
  it("al cambiar el activo de una fila, quita el «repetido» de la que ya no lo está", () => {
    const before = [emptyLine(ref("A"), "50"), emptyLine(ref("A"), "50")];
    const errors = { lines: [{}, { asset: DUPLICATE_ASSET }], total: "x" };
    const after = [{ ...before[0]!, asset: ref("B") }, before[1]!];
    expect(carryLineErrors(errors, before, after)).toEqual({ lines: [{}, {}] });
  });

  it("mantiene el «repetido» si una fila anterior sigue con el mismo activo", () => {
    const before = [emptyLine(ref("A")), emptyLine(ref("A")), emptyLine(ref("A"))];
    const errors = { lines: [{}, { asset: DUPLICATE_ASSET }, { asset: DUPLICATE_ASSET, percent: "p" }] };
    const after = [before[0]!, { ...before[1]!, asset: ref("B") }, before[2]!];
    expect(carryLineErrors(errors, before, after).lines).toEqual([
      {},
      {},
      { asset: DUPLICATE_ASSET, percent: "p" },
    ]);
  });
});
