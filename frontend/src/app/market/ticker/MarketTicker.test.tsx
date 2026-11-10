import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import type { TickerOut } from "../../../api/generated/schema";
import mock from "../../../api/mocks/TickerOut.json";
import { TickerStrip } from "./MarketTicker";

const ITEMS = (mock as TickerOut).items;
const QUOTED = ITEMS.filter((i) => i.change_pct !== null);

function setReducedMotion(reduce: boolean) {
  vi.stubGlobal(
    "matchMedia",
    (query: string) =>
      ({
        matches: reduce && query.includes("prefers-reduced-motion"),
        media: query,
        addEventListener: () => {},
        removeEventListener: () => {},
      }) as unknown as MediaQueryList,
  );
}

const track = () => document.querySelector<HTMLElement>("[data-state]")!;
const lists = () => screen.getByRole("region", { name: "Tus activos" }).querySelectorAll("ul");

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("TickerStrip", () => {
  it("enseña precio, variación con signo y palabra, y la fecha del cierre", () => {
    setReducedMotion(false);
    render(<TickerStrip items={ITEMS} />);
    const first = within(lists()[0]!);
    expect(first.getByText("IWDA")).toBeTruthy();
    expect(first.getByText(/95,42\s€/)).toBeTruthy();
    expect(first.getByText("-0,7 %")).toBeTruthy();
    expect(first.getByText("baja")).toBeTruthy();
    expect(first.getByText("6 nov")).toBeTruthy();
    expect(first.getByText("-0,7 %").closest("[data-calc-id]")?.getAttribute("data-calc-id")).toBe(
      QUOTED[0]!.calc_id,
    );
  });

  it("no enseña los activos sin variación (precio fijo)", () => {
    setReducedMotion(false);
    render(<TickerStrip items={ITEMS} />);
    expect(within(lists()[0]!).getAllByRole("listitem")).toHaveLength(QUOTED.length);
    expect(screen.queryByText(/Depósito/)).toBeNull();
  });

  it("sin activos con variación no pinta nada", () => {
    setReducedMotion(false);
    const fixed = ITEMS.filter((i) => i.change_pct === null);
    const { container } = render(<TickerStrip items={fixed} />);
    expect(container.innerHTML).toBe("");
  });

  it("las copias que llenan el bucle no se anuncian ni reciben el foco", () => {
    setReducedMotion(false);
    render(<TickerStrip items={ITEMS} />);
    const [first, ...rest] = Array.from(lists());
    // Dos mitades iguales con al menos 8 entradas cada una (un solo activo con variación: 8 + 8).
    expect(rest.length + 1).toBe(16);
    expect(first!.hasAttribute("aria-hidden")).toBe(false);
    for (const copy of rest) {
      expect(copy.getAttribute("aria-hidden")).toBe("true");
      expect(copy.hasAttribute("inert")).toBe(true);
    }
  });

  it("se pausa con el botón, con el ratón encima y con el foco dentro", () => {
    setReducedMotion(false);
    render(<TickerStrip items={ITEMS} />);
    const region = screen.getByRole("region", { name: "Tus activos" });
    expect(track().dataset.state).toBe("running");

    fireEvent.click(screen.getByRole("button", { name: "Pausar el desplazamiento de precios" }));
    expect(track().dataset.state).toBe("paused");
    fireEvent.click(screen.getByRole("button", { name: "Reanudar el desplazamiento de precios" }));
    expect(track().dataset.state).toBe("running");

    fireEvent.mouseEnter(region);
    expect(track().dataset.state).toBe("paused");
    fireEvent.mouseLeave(region);
    expect(track().dataset.state).toBe("running");

    fireEvent.focus(screen.getByRole("button"));
    expect(track().dataset.state).toBe("paused");
    fireEvent.blur(screen.getByRole("button"));
    expect(track().dataset.state).toBe("running");
  });

  it("con prefers-reduced-motion no se mueve: una sola lista y sin botón de pausa", () => {
    setReducedMotion(true);
    render(<TickerStrip items={ITEMS} />);
    expect(lists()).toHaveLength(1);
    expect(track().classList.contains("kairos-ticker-track")).toBe(false);
    expect(screen.queryByRole("button")).toBeNull();
  });
});
