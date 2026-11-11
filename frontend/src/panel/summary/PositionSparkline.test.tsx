import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import history from "../../api/mocks/AssetHistoryOut.json";
import { PositionSparkline } from "./PositionSparkline";

const NVDA = "US67066G1040";

const json = (body: unknown, code = 200) =>
  new Response(JSON.stringify(body), { status: code, headers: { "Content-Type": "application/json" } });

function stubApi(body: unknown, code = 200) {
  const fetchMock = vi.fn<(input: RequestInfo | URL) => Promise<Response>>(async () => json(body, code));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderSparkline() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <PositionSparkline portfolioId="laura" assetId={NVDA} name="NVIDIA Corp." />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("PositionSparkline", () => {
  it("pide la serie de un mes y la resume con los precios de la API, sin variación calculada", async () => {
    const fetchMock = stubApi(history);
    renderSparkline();
    const img = await screen.findByRole("img");
    const label = img.getAttribute("aria-label") ?? "";
    // Primer cierre del mock: 185.20000000 USD.
    expect(label).toMatch(/^Precio de NVIDIA Corp\. en el último mes: \d+ cierres, de 185,20\sUS\$ a /);
    expect(label).not.toMatch(/sube|baja|%/);
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain(`/portfolios/laura/positions/${NVDA}/history?period=1m`);
  });

  it("si la API no tiene la serie, dice que no hay datos en lugar de dibujar", async () => {
    // 404: el hook no lo reintenta (un 503 sí, con espera).
    stubApi({ code: "NOT_FOUND", message: "No", details: {} }, 404);
    renderSparkline();
    expect(await screen.findByText("Sin datos")).toBeDefined();
    expect(screen.queryByRole("img")).toBeNull();
  });
});
