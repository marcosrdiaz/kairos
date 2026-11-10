import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import type { StatusOut } from "../api/generated/schema";
import atento from "../api/mocks/StatusOut.json";
import revisaPlan from "../api/mocks/StatusOut.revisa_plan.json";
import tranquilo from "../api/mocks/StatusOut.tranquilo.json";
import { HomeWidget } from "./HomeWidget";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

const CASES: [string, StatusOut, string][] = [
  ["tranquilo", tranquilo as StatusOut, "Tranquilo"],
  ["atento", atento as StatusOut, "Atento"],
  ["revisa_plan", revisaPlan as StatusOut, "Revisa tu plan"],
];

describe("HomeWidget", () => {
  it.each(CASES)("estado %s: color + palabra, cifra y frase completa", (state, status, word) => {
    const { container } = render(
      <MemoryRouter>
        <HomeWidget status={status} href="/inicio?p=laura" />
      </MemoryRouter>,
    );
    const badge = container.querySelector(`[data-state="${state}"]`);
    expect(badge?.textContent).toContain(word);
    // En el widget la frase va completa, con su "Toca para ver…".
    expect(screen.getByText(status.sentence)).toBeTruthy();
    expect(screen.getByText(/34\.311,68\s€/)).toBeTruthy();
  });

  it("al cambiar el estado, la frase nueva está una sola vez y la antigua solo oculta al lector", () => {
    vi.useFakeTimers();
    const view = render(
      <MemoryRouter>
        <HomeWidget status={tranquilo as StatusOut} href="/inicio?p=laura" />
      </MemoryRouter>,
    );
    view.rerender(
      <MemoryRouter>
        <HomeWidget status={atento as StatusOut} href="/inicio?p=laura" />
      </MemoryRouter>,
    );
    expect(screen.getAllByText(atento.sentence)).toHaveLength(1);
    expect(screen.getByText(tranquilo.sentence).closest("[aria-hidden='true']")).not.toBeNull();
    act(() => {
      vi.advanceTimersByTime(400);
    });
    expect(screen.queryByText(tranquilo.sentence)).toBeNull();
    expect(screen.getAllByText(atento.sentence)).toHaveLength(1);
  });

  it("es un único enlace a Inicio con nombre accesible y traza", () => {
    render(
      <MemoryRouter>
        <HomeWidget status={atento as StatusOut} href="/inicio?p=laura" />
      </MemoryRouter>,
    );
    const link = screen.getByRole("link");
    expect(link.getAttribute("href")).toBe("/inicio?p=laura");
    expect(link.getAttribute("aria-label")).toContain("Atento");
    expect(link.getAttribute("aria-label")).toContain(atento.sentence);
    expect(link.getAttribute("data-calc-id")).toBe(atento.calc_id);
  });
});
