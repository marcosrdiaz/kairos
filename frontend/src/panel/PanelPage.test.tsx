import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import bce from "../api/mocks/EventImpactOut.json";
import nvda from "../api/mocks/EventImpactOut.nvda.json";
import javier from "../api/mocks/PortfolioOut.javier.json";
import laura from "../api/mocks/PortfolioOut.json";
import status from "../api/mocks/StatusOut.json";
import { PanelPage } from "./PanelPage";

const PORTFOLIOS = [
  { id: "laura", name: "Laura", profile: "dinamico" },
  { id: "javier", name: "Javier", profile: "moderado" },
];

const json = (body: unknown, code = 200) =>
  new Response(JSON.stringify(body), { status: code, headers: { "Content-Type": "application/json" } });

/** Backend falso: sirve cada ruta según la cartera pedida. `events` por cartera. */
function stubApi(events: Record<string, unknown[] | "error"> = { laura: [bce, nvda], javier: [nvda] }) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/portfolios")) return json(PORTFOLIOS);
      const id = /portfolios\/(\w+)/.exec(url)?.[1] ?? "laura";
      if (url.includes("/status")) return json({ ...status, state: "atento" });
      if (url.includes("/events")) {
        const list = events[id];
        return list === "error" ? json({ code: "INTERNAL" }, 500) : json(list ?? []);
      }
      return json(id === "javier" ? javier : laura);
    }),
  );
}

function LocationProbe() {
  const { search } = useLocation();
  return <div data-testid="search">{search}</div>;
}

function renderPanel(path = "/panel?p=laura") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <PanelPage />
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("PanelPage · Resumen", () => {
  it("muestra patrimonio exacto con fecha, estado con palabra y posiciones con la fecha de su precio", async () => {
    stubApi();
    renderPanel();
    const dl = await screen.findByText("Patrimonio");
    expect(dl.parentElement?.textContent).toMatch(/34\.311,68\s€/);
    expect(dl.parentElement?.textContent).toMatch(/Valorado a/);
    expect(await screen.findByText("Atento")).toBeTruthy();
    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");
    expect(rows.length).toBe(laura.positions.length + 1);
    expect(within(table).getAllByText(/6 de noviembre de 2026/).length).toBeGreaterThan(0);
    expect(table.querySelector("[data-calc-id]")).not.toBeNull();
  });

  it("deja el hueco de los avisos de T2-12", async () => {
    stubApi();
    const { container } = renderPanel();
    await screen.findByText("Patrimonio");
    expect(container.querySelector('[data-slot="panel-notices"]')).not.toBeNull();
  });
});

describe("PanelPage · Eventos", () => {
  it("pinta cada evento con cadena causal, rango y confianza, nunca cifra exacta", async () => {
    stubApi();
    renderPanel();
    expect(await screen.findByRole("heading", { level: 3, name: bce.title })).toBeTruthy();
    expect(screen.getAllByText(/entre -10\s€ y 190\s€/).length).toBe(1);
    expect(screen.getAllByText(/^Confianza (alta|media|baja)$/).length).toBe(2);
    expect(screen.getAllByRole("list", { name: "Cadena causal" }).length).toBe(2);
    expect(screen.queryByText(/90,00\s€/)).toBeNull();
  });

  it("sin eventos, lo dice sin inventar cifras", async () => {
    stubApi({ laura: [], javier: [] });
    renderPanel();
    expect(await screen.findByText(/Ningún evento reciente afecta/)).toBeTruthy();
  });

  it("si falla el backend, muestra un estado vacío honesto", async () => {
    stubApi({ laura: "error", javier: [] });
    renderPanel();
    expect(await screen.findByText(/no podemos mostrar los eventos/)).toBeTruthy();
  });
});

describe("PanelPage · cambio de cartera", () => {
  it("un clic en Javier cambia los datos y mantiene ?p= para enlazar", async () => {
    stubApi();
    renderPanel();
    await screen.findByRole("heading", { level: 3, name: bce.title });
    fireEvent.click(await screen.findByRole("radio", { name: "Javier" }));
    expect(screen.getByTestId("search").textContent).toBe("?p=javier");
    await waitFor(() => expect(screen.queryByRole("heading", { level: 3, name: bce.title })).toBeNull());
    expect(await screen.findByRole("heading", { level: 3, name: nvda.title })).toBeTruthy();
    expect((await screen.findByText("Patrimonio")).parentElement?.textContent).toMatch(/\d/);
    expect(document.querySelector("header [role=status]")?.textContent).toContain("Javier");
  });
});
