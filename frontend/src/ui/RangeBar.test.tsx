import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { RangeBar } from "./RangeBar";
import { rangeBarLayout } from "./range-bar-geometry";

afterEach(cleanup);

describe("rangeBarLayout", () => {
  it("el carril va del rango al cero, con un margen del 5 % a cada lado", () => {
    const layout = rangeBarLayout(-10, 190, 90);
    expect(layout).not.toBeNull();
    // dominio [-10, 190] + 10 de margen: [-20, 200]
    expect(layout!.start).toBeCloseTo(10 / 220);
    expect(layout!.end).toBeCloseTo(210 / 220);
    expect(layout!.center).toBeCloseTo(110 / 220);
    expect(layout!.zero).toBeCloseTo(20 / 220);
  });

  it("un rango negativo lejos del cero queda a la izquierda y estrecho", () => {
    const layout = rangeBarLayout(-349, -325, -337)!;
    expect(layout.start).toBeLessThan(0.1);
    expect(layout.end - layout.start).toBeLessThan(0.1);
    expect(layout.zero).toBeGreaterThan(layout.end);
  });

  it("un rango positivo deja el cero a la izquierda", () => {
    const layout = rangeBarLayout(100, 300, 200)!;
    expect(layout.zero).toBeLessThan(layout.start);
  });

  it("acepta los extremos en cualquier orden", () => {
    expect(rangeBarLayout(190, -10, 90)).toEqual(rangeBarLayout(-10, 190, 90));
  });

  it("sin rango (extremos iguales o no numéricos) no hay barra", () => {
    expect(rangeBarLayout(-224, -224, -224)).toBeNull();
    expect(rangeBarLayout(Number.NaN, 10, 5)).toBeNull();
  });

  it("un centro fuera del rango se queda en el borde", () => {
    const layout = rangeBarLayout(0, 100, 150)!;
    expect(layout.center).toBeCloseTo(layout.end);
  });
});

describe("RangeBar", () => {
  const label = "Rango del impacto estimado: entre -10 € y 190 €, centro ≈ 90 €";

  it("es una imagen con la lectura en aria-label y sin texto visible", () => {
    const { container } = render(<RangeBar low={-10} high={190} center={90} label={label} />);
    const img = screen.getByRole("img", { name: label });
    expect(img.textContent).toBe("");
    expect(container.textContent).toBe("");
  });

  it("marca el centro y la línea del cero", () => {
    const { container } = render(<RangeBar low={-10} high={190} center={90} label={label} />);
    expect(container.querySelector('[data-slot="range-bar-center"]')).not.toBeNull();
    expect(container.querySelector('[data-slot="range-bar-zero"]')).not.toBeNull();
  });

  it("la línea del cero sale también con un rango lejos de él", () => {
    const { container } = render(<RangeBar low={-349} high={-325} center={-337} label={label} />);
    expect(container.querySelector('[data-slot="range-bar-zero"]')).not.toBeNull();
  });

  it("la confianza solo cambia la opacidad del tramo", () => {
    const opacity = (confidence: "alta" | "media" | "baja") => {
      const { container, unmount } = render(
        <RangeBar low={-10} high={190} center={90} label={label} confidence={confidence} />,
      );
      const fill = container.querySelector<HTMLElement>('[data-slot="range-bar-fill"]');
      const value = Number(fill?.style.opacity);
      unmount();
      return value;
    };
    expect(opacity("alta")).toBeGreaterThan(opacity("media"));
    expect(opacity("media")).toBeGreaterThan(opacity("baja"));
  });

  it("sin rango no pinta nada", () => {
    const { container } = render(<RangeBar low={-224} high={-224} center={-224} label={label} />);
    expect(container.firstChild).toBeNull();
  });
});
