import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import history from "../../../api/mocks/AssetHistoryOut.json";
import ticker from "../../../api/mocks/TickerOut.json";
import type { TickerItemOut } from "../../../api/generated/schema";
import { TickerStrip } from "../ticker/MarketTicker";
import { AssetChart } from "./AssetChart";
import { assetHref } from "./assetHref";

const NVDA = "US67066G1040";

const json = (body: unknown, code = 200) =>
  new Response(JSON.stringify(body), { status: code, headers: { "Content-Type": "application/json" } });

function stubApi(code = 200) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/events")) return json([]);
    if (code !== 200) return json({ code: "NOT_FOUND", message: "No", details: {} }, code);
    const period = new URL(url, "http://x").searchParams.get("period");
    return json({ ...history, period });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderChart() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <AssetChart portfolioId="laura" assetId={NVDA} />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("AssetChart", () => {
  it("pide la serie de la posición y muestra valor, precio en su divisa y participaciones", async () => {
    const fetchMock = stubApi();
    renderChart();
    const lastClose = await screen.findByText(/Último cierre: 6 de noviembre de 2026/);
    expect(lastClose.parentElement?.textContent).toMatch(/Precio: 197,45\sUS\$.*7,4 participaciones/);
    expect(screen.getByRole("heading", { name: "Evolución de NVIDIA Corp." })).toBeDefined();
    // Encima, el valor de la posición en el último cierre (con su traza).
    expect(lastClose.parentElement?.previousElementSibling?.textContent).toMatch(/1\.?258,67\s€.*\+22,65/);
    const urls = fetchMock.mock.calls.map(([u]) => String(u));
    expect(urls.some((u) => u.includes(`/portfolios/laura/positions/${NVDA}/history?period=1y`))).toBe(true);
  });

  it("si la cartera nunca tuvo el activo, lo dice en lugar de dibujar nada", async () => {
    stubApi(404);
    renderChart();
    expect(await screen.findByText("Esta cartera no ha tenido nunca ese activo.")).toBeDefined();
    expect(screen.queryByText(/Último cierre/)).toBeNull();
  });
});

describe("enlaces a la evolución de una posición", () => {
  it("la ruta conserva la cartera elegida", () => {
    expect(assetHref(NVDA, "javier")).toBe(`/activo/${NVDA}?p=javier`);
  });

  it("cada activo del ticker enlaza a su evolución", () => {
    const items = (ticker as { items: TickerItemOut[] }).items;
    render(
      <MemoryRouter>
        <TickerStrip items={items} hrefFor={(id) => assetHref(id, "laura")} />
      </MemoryRouter>,
    );
    const quoted = items.filter((i) => i.change_pct !== null && i.change_pct !== undefined);
    const first = quoted[0]!;
    const link = screen.getAllByRole("link", { name: first.ticker ?? first.name })[0];
    expect(link?.getAttribute("href")).toBe(`/activo/${first.asset_id}?p=laura`);
  });
});
