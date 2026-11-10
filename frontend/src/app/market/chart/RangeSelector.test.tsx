import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { RangeSelector } from "./RangeSelector";
import type { ChartRow } from "./chartFormat";

afterEach(cleanup);

const ROWS: ChartRow[] = Array.from({ length: 20 }, (_, i) => ({
  date: `2026-10-${String(i + 1).padStart(2, "0")}T00:00:00Z`,
  value: 100 + i,
  raw: `${100 + i}.00`,
  change: i === 0 ? null : "1.00",
  pct: i === 0 ? null : "0.0100",
  flows: "0.00",
  hasFlow: false,
}));

function renderRange(start = 0, end = ROWS.length - 1) {
  const onChange = vi.fn();
  render(<RangeSelector rows={ROWS} start={start} end={end} onChange={onChange} />);
  return onChange;
}

describe("RangeSelector", () => {
  it("cada tirador es un slider con nombre y su fecha como valor", () => {
    renderRange(2, 15);
    const from = screen.getByRole("slider", { name: "Inicio del rango visible" });
    const to = screen.getByRole("slider", { name: "Fin del rango visible" });
    expect(from.getAttribute("aria-valuenow")).toBe("2");
    expect(from.getAttribute("aria-valuetext")).toBe("3 de octubre de 2026");
    expect(to.getAttribute("aria-valuetext")).toBe("16 de octubre de 2026");
  });

  it("las flechas mueven un día, AvPág/RePág un 10 % e Inicio/Fin hasta el borde", () => {
    const onChange = renderRange(5, 15);
    const from = screen.getByRole("slider", { name: "Inicio del rango visible" });
    const to = screen.getByRole("slider", { name: "Fin del rango visible" });
    fireEvent.keyDown(from, { key: "ArrowLeft" });
    expect(onChange).toHaveBeenLastCalledWith(4, 15);
    fireEvent.keyDown(to, { key: "PageDown" });
    expect(onChange).toHaveBeenLastCalledWith(5, 13);
    fireEvent.keyDown(from, { key: "Home" });
    expect(onChange).toHaveBeenLastCalledWith(0, 15);
    fireEvent.keyDown(to, { key: "End" });
    expect(onChange).toHaveBeenLastCalledWith(5, 19);
  });

  it("el inicio nunca alcanza al fin (quedan al menos dos puntos)", () => {
    const onChange = renderRange(9, 10);
    fireEvent.keyDown(screen.getByRole("slider", { name: "Inicio del rango visible" }), { key: "End" });
    expect(onChange).toHaveBeenLastCalledWith(9, 10);
  });
});
