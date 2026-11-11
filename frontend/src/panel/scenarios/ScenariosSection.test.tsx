import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import scenario from "../../api/mocks/ScenarioOut.json";
import { ScenariosSection } from "./ScenariosSection";

const json = (body: unknown, code = 200) =>
  new Response(JSON.stringify(body), { status: code, headers: { "Content-Type": "application/json" } });

function renderSection() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ScenariosSection portfolioId="laura" />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ScenariosSection", () => {
  it("no llama al backend hasta que se elige un supuesto", () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    renderSection();
    expect(screen.getByText(/Elige un supuesto para ver/)).toBeTruthy();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("envía los shocks del supuesto y pinta rango, confianza e impacto por activo trazable", async () => {
    const fetch = vi.fn(async () => json(scenario));
    vi.stubGlobal("fetch", fetch);
    renderSection();
    const button = screen.getByRole("button", { name: "La bolsa mundial cae un 10 %" });
    fireEvent.click(button);
    expect(button.getAttribute("aria-pressed")).toBe("true");

    const table = await screen.findByRole("list", { name: "Impacto estimado por activo" });
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/v1/portfolios/laura/scenarios");
    expect(JSON.parse(String(init.body))).toEqual({ factor_shocks: { EQ_GLOBAL: "-0.10" } });

    expect(screen.getByText(/entre -2\.?890\s€ y -1\.?930\s€/)).toBeTruthy();
    expect(screen.getByText("Confianza alta")).toBeTruthy();
    const rows = within(table).getAllByRole("listitem");
    expect(rows.length).toBe(scenario.breakdown.length);
    expect(within(rows[0]!).getByText(/^≈ -1\.?090\s€$/)).toBeTruthy();
    expect(table.querySelector("[data-calc-id]")).not.toBeNull();
  });

  it("nunca da una cifra exacta del total ni habla de comprar o vender", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => json(scenario)));
    const { container } = renderSection();
    fireEvent.click(screen.getByRole("button", { name: "La bolsa mundial cae un 10 %" }));
    await screen.findByRole("list", { name: "Impacto estimado por activo" });
    expect(screen.queryByText(/-2\.?410/)).toBeNull();
    expect(container.textContent).not.toMatch(/\b(compra|vende|te recomiendo|deberías)\b/i);
  });

  it("si el backend falla, lo dice sin inventar cifras", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => json({ code: "INTERNAL" }, 500)));
    renderSection();
    fireEvent.click(screen.getByRole("button", { name: "El petróleo sube un 20 %" }));
    expect(await screen.findByText(/no podemos calcular este escenario/)).toBeTruthy();
    expect(screen.queryByRole("table")).toBeNull();
  });
});
