import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import type { StatusOut } from "../api/generated/schema";
import atento from "../api/mocks/StatusOut.json";
import revisaPlan from "../api/mocks/StatusOut.revisa_plan.json";
import tranquilo from "../api/mocks/StatusOut.tranquilo.json";
import { StatusCard } from "./StatusCard";
import { StatusTiles } from "./StatusTiles";
import { signedPercent, trendOf, withoutTapHint } from "./states";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

function renderStatus(status: StatusOut) {
  return render(
    <MemoryRouter>
      <StatusCard status={status} />
      <StatusTiles status={status} />
    </MemoryRouter>,
  );
}

const CASES: [string, StatusOut, string][] = [
  ["tranquilo", tranquilo as StatusOut, "Tranquilo"],
  ["atento", atento as StatusOut, "Atento"],
  ["revisa_plan", revisaPlan as StatusOut, "Revisa tu plan"],
];

/** Valor de la pareja <dt>/<dd> con ese término. */
function definition(term: string): string {
  const dt = screen.getByText(term, { selector: "dt" });
  return dt.nextElementSibling?.textContent ?? "";
}

describe("StatusCard + StatusTiles", () => {
  it.each(CASES)(
    "estado %s: color + palabra, frase como titular y traza",
    (state, status, word) => {
      const { container } = renderStatus(status);
      const badge = container.querySelector(`[data-state="${state}"]`);
      expect(badge?.textContent).toContain(word);
      expect(
        screen.getByRole("heading", {
          level: 2,
          name: withoutTapHint(status.sentence),
        }),
      ).toBeTruthy();
      expect(container.querySelector(`[data-calc-id="${status.calc_id}"]`)).not.toBeNull();
    },
  );

  it("el valor total está en Tu cartera hoy y las demás cifras en la lista de descripción", () => {
    renderStatus(atento as StatusOut);
    expect(screen.getByRole("region").textContent).toMatch(/Tu cartera hoy.*34\.311,68\s€/);
    expect(screen.queryByText("Valor total", { selector: "dt" })).toBeNull();
    expect(definition("Esta semana")).toMatch(/-1,5\s%/);
    expect(definition("Motivo del estado")).toBe("Un evento reciente");
    expect(definition("Precios a")).toBe("6 de noviembre de 2026");
  });

  it("solo ofrece 'Ver por qué' si hay motivo", () => {
    renderStatus(tranquilo as StatusOut);
    expect(screen.queryByRole("link", { name: /Ver por qué/ })).toBeNull();
    cleanup();
    renderStatus(atento as StatusOut);
    expect(screen.getByRole("link", { name: /Ver por qué/ })).toBeTruthy();
  });

  it("anuncia el estado con aria-live", () => {
    const { container } = renderStatus(atento as StatusOut);
    const live = container.querySelector('[aria-live="polite"]') as HTMLElement;
    expect(within(live).getByText("Atento")).toBeTruthy();
  });

  it("al cambiar el estado, la frase nueva está una sola vez y la antigua solo oculta al lector", () => {
    vi.useFakeTimers();
    const view = renderStatus(tranquilo as StatusOut);
    const before = withoutTapHint((tranquilo as StatusOut).sentence);
    const after = withoutTapHint((atento as StatusOut).sentence);
    view.rerender(
      <MemoryRouter>
        <StatusCard status={atento as StatusOut} />
        <StatusTiles status={atento as StatusOut} />
      </MemoryRouter>,
    );
    // Durante el fundido.
    expect(screen.getAllByText(after)).toHaveLength(1);
    expect(screen.getByText(before).closest("[aria-hidden='true']")).not.toBeNull();
    expect(screen.getByRole("heading", { level: 2, name: after })).toBeTruthy();
    // Después.
    act(() => {
      vi.advanceTimersByTime(400);
    });
    expect(screen.queryByText(before)).toBeNull();
    expect(screen.getAllByText(after)).toHaveLength(1);
  });

  it("los iconos son decorativos", () => {
    const { container } = renderStatus(atento as StatusOut);
    for (const svg of container.querySelectorAll("svg")) {
      expect(svg.getAttribute("aria-hidden")).toBe("true");
    }
  });
});

describe("withoutTapHint", () => {
  it.each([
    [
      "Tus fondos tecnológicos caen tras resultados. Toca para ver por qué.",
      "Tus fondos tecnológicos caen tras resultados.",
    ],
    [
      "Tu cartera se ha alejado de tu plan. Toca para ver cuánto.",
      "Tu cartera se ha alejado de tu plan.",
    ],
    ["Tu cartera sigue en línea con tu plan.", "Tu cartera sigue en línea con tu plan."],
    ["Toca para ver por qué.", "Toca para ver por qué."],
  ])("%s -> %s", (input, expected) => {
    expect(withoutTapHint(input)).toBe(expected);
  });
});

describe("variación semanal", () => {
  it.each([
    ["-0.015", "-1,5 %", "down"],
    ["0.012", "+1,2 %", "up"],
    ["0", "0,0 %", "flat"],
    ["0.000", "0,0 %", "flat"],
  ])("%s -> %s (%s)", (input, text, trend) => {
    expect(signedPercent(input)).toBe(text);
    expect(trendOf(input)).toBe(trend);
  });
});
