import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import type { StatusOut } from "../api/generated/schema";
import atento from "../api/mocks/StatusOut.json";
import revisaPlan from "../api/mocks/StatusOut.revisa_plan.json";
import tranquilo from "../api/mocks/StatusOut.tranquilo.json";
import { StatusCard } from "./StatusCard";

afterEach(cleanup);

function renderCard(status: StatusOut) {
  return render(
    <MemoryRouter>
      <StatusCard status={status} />
    </MemoryRouter>,
  );
}

const CASES: [string, StatusOut, string][] = [
  ["tranquilo", tranquilo as StatusOut, "Tranquilo"],
  ["atento", atento as StatusOut, "Atento"],
  ["revisa_plan", revisaPlan as StatusOut, "Revisa tu plan"],
];

describe("StatusCard", () => {
  it.each(CASES)("estado %s: color + palabra, cifra y frase", (state, status, word) => {
    const { container } = renderCard(status);
    const badge = container.querySelector(`[data-state="${state}"]`);
    expect(badge).not.toBeNull();
    expect(badge?.textContent).toContain(word);
    expect(screen.getByText(status.sentence)).toBeTruthy();
    expect(screen.getByText(/34\.311,68\s€/)).toBeTruthy();
    expect(screen.getByText(/-1,5\s%/)).toBeTruthy();
    expect(container.querySelector(`[data-calc-id="${status.calc_id}"]`)).not.toBeNull();
  });

  it("solo ofrece 'Ver por qué' si hay motivo", () => {
    renderCard(tranquilo as StatusOut);
    expect(screen.queryByRole("link", { name: "Ver por qué" })).toBeNull();
    cleanup();
    renderCard(atento as StatusOut);
    expect(screen.getByRole("link", { name: "Ver por qué" })).toBeTruthy();
  });

  it("muestra la fecha del precio", () => {
    renderCard(tranquilo as StatusOut);
    expect(screen.getByText(/Precios a 6 de noviembre de 2026/)).toBeTruthy();
  });

  it("anuncia el cambio de estado con aria-live", () => {
    const { container } = renderCard(atento as StatusOut);
    const live = container.querySelector('[aria-live="polite"]');
    expect(live?.textContent).toContain("Atento");
  });
});
