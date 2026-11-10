import { describe, expect, it } from "vitest";
import { computeBandLayout, nearestIndex, type BandDatum } from "./band-geometry";

const padding = { top: 0, right: 0, bottom: 0, left: 0 };
const data: BandDatum[] = [
  { x: 0, mid: 10, low: 10, high: 10 },
  { x: 1, mid: 12, low: 12, high: 12 },
  { x: 2, mid: 14, low: 10, high: 18 },
];

describe("computeBandLayout", () => {
  const layout = computeBandLayout(data, { width: 200, height: 100, padding, splitIndex: 1 });

  it("coloca el borde alto por encima (y menor) del bajo", () => {
    const last = layout.points[2];
    expect(last).toBeDefined();
    expect(last!.high).toBeLessThan(last!.mid);
    expect(last!.mid).toBeLessThan(last!.low);
  });

  it("la banda se cierra donde el rango se abre y es una línea donde no hay rango", () => {
    expect(layout.points[0]!.low).toBe(layout.points[0]!.high);
    expect(layout.bandPath).not.toBe("");
    expect(layout.upperPath).not.toBe(layout.lowerPath);
  });

  it("el tramo observado y el estimado se tocan en el punto de corte", () => {
    expect(layout.observedPath.startsWith("M")).toBe(true);
    expect(layout.estimatedPath.startsWith("M")).toBe(true);
    expect(layout.observedPath).not.toBe(layout.estimatedPath);
  });

  it("el dominio incluye los bordes de la banda", () => {
    const ys = layout.points.flatMap((p) => [p.low, p.high]);
    expect(Math.min(...ys)).toBeGreaterThanOrEqual(0);
    expect(Math.max(...ys)).toBeLessThanOrEqual(100);
  });

  it("no rompe con una serie vacía", () => {
    const empty = computeBandLayout([], { width: 100, height: 50, padding, splitIndex: 0 });
    expect(empty.points).toEqual([]);
  });
});

describe("nearestIndex", () => {
  it("elige el punto más cercano y devuelve null si no hay", () => {
    const { points } = computeBandLayout(data, { width: 200, height: 100, padding, splitIndex: 1 });
    expect(nearestIndex(points, 5)).toBe(0);
    expect(nearestIndex(points, 110)).toBe(1);
    expect(nearestIndex(points, 999)).toBe(2);
    expect(nearestIndex([], 5)).toBeNull();
  });
});
