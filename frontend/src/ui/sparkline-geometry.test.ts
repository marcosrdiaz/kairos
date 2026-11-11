import { describe, expect, it } from "vitest";
import {
  areaPath,
  computeDomain,
  computeLayout,
  describeSeries,
  indexAtX,
  linePath,
  uniformPadding,
} from "./sparkline-geometry";

const fmt = (n: number) => String(n);

describe("computeDomain", () => {
  it("abarca los datos y centra una serie plana", () => {
    expect(computeDomain([3, 1, 2])).toEqual([1, 3]);
    expect(computeDomain([5, 5])).toEqual([4, 6]);
    expect(computeDomain([])).toEqual([0, 1]);
  });

  it("incluye el cero y los valores extra si se piden", () => {
    expect(computeDomain([2, 4], { includeZero: true })).toEqual([0, 4]);
    expect(computeDomain([2, 4], { extra: [9] })).toEqual([2, 9]);
  });
});

describe("computeLayout", () => {
  it("coloca el mínimo abajo y el máximo arriba", () => {
    const layout = computeLayout([0, 10], {
      width: 100,
      height: 50,
      padding: uniformPadding(0),
      domain: [0, 10],
    });
    expect(layout.points[0]).toMatchObject({ x: 0, y: 50 });
    expect(layout.points[1]).toMatchObject({ x: 100, y: 0 });
    expect(layout.baselineY).toBe(50);
  });

  it("deja un hueco (NaN) donde falta el dato y no lo dibuja", () => {
    const layout = computeLayout([1, Number.NaN, 3], {
      width: 100,
      height: 50,
      padding: uniformPadding(0),
      domain: [1, 3],
    });
    expect(Number.isNaN(layout.points[1]?.y)).toBe(true);
    // Con el hueco en medio, los dos puntos no se unen con una línea.
    expect(linePath(layout.points, "linear")).not.toContain("L");
    expect(areaPath(layout.points, layout.baselineY, "linear")).toContain("Z");
  });
});

describe("indexAtX", () => {
  const opts = { count: 5, width: 100, padding: uniformPadding(0) };
  it("devuelve el dato más cercano y se queda dentro de la serie", () => {
    expect(indexAtX(0, opts)).toBe(0);
    expect(indexAtX(49, opts)).toBe(2);
    expect(indexAtX(500, opts)).toBe(4);
    expect(indexAtX(-20, opts)).toBe(0);
    expect(indexAtX(10, { ...opts, count: 0 })).toBeNull();
  });
});

describe("describeSeries", () => {
  it("resume la serie en español", () => {
    expect(describeSeries([100, 135], fmt)).toBe("2 puntos, de 100 a 135");
    expect(describeSeries([100, 50], fmt)).toBe("2 puntos, de 100 a 50");
    // Sin variación calculada en el cliente: ni «sube» ni «baja» ni %.
    expect(describeSeries([100, 135, 150], fmt)).not.toMatch(/sube|baja|%/);
    expect(describeSeries([], fmt)).toBe("Sin datos");
  });
});
