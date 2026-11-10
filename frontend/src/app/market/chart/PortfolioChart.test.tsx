import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import history from "../../../api/mocks/PortfolioHistoryOut.json";
import { PortfolioChart } from "./PortfolioChart";
import { niceScale, tickDate, tickEur } from "./chartFormat";

const json = (body: unknown, code = 200) =>
  new Response(JSON.stringify(body), { status: code, headers: { "Content-Type": "application/json" } });

function stubApi(body: unknown = history, code = 200) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const period = new URL(String(input), "http://x").searchParams.get("period");
    return json(code === 200 ? { ...(body as object), period } : body, code);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderChart() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <PortfolioChart portfolioId="laura" />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("PortfolioChart", () => {
  it("pide el último año por defecto y muestra el último cierre", async () => {
    const fetchMock = stubApi();
    renderChart();
    const lastClose = await screen.findByText(/Último cierre: 6 de noviembre de 2026/);
    // En una sola línea: último cierre, valor al empezar y aportaciones.
    const line = lastClose.parentElement;
    expect(line?.textContent).toMatch(
      /Último cierre: 6 de noviembre de 2026.*Al empezar el periodo: 33\.410,25.*Sin aportaciones ni retiradas/,
    );
    expect(line?.previousElementSibling?.textContent).toMatch(/34\.311,68/);
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("/portfolios/laura/history?period=1y");
    expect(screen.getByRole("radio", { name: "Último año" })).toHaveProperty("checked", true);
  });

  it("ofrece 1 semana, 1 mes, 6 meses, 1 año y todo", async () => {
    stubApi();
    renderChart();
    await screen.findByText(/Último cierre/);
    const names = screen.getAllByRole("radio").map((r) => r.getAttribute("aria-label"));
    expect(names).toEqual(["Última semana", "Último mes", "Últimos 6 meses", "Último año", "Todo el historial"]);
  });

  it("cambiar de periodo pide la serie de ese periodo", async () => {
    const fetchMock = stubApi();
    renderChart();
    await screen.findByText(/Último cierre/);
    fireEvent.click(screen.getByRole("radio", { name: "Última semana" }));
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([url]) => String(url).includes("period=1w"))).toBe(true),
    );
    expect(screen.getByRole("radio", { name: "Última semana" })).toHaveProperty("checked", true);
  });

  it("tiene una tabla alternativa con todos los puntos, agrupados por mes y del más reciente", async () => {
    stubApi();
    renderChart();
    const table = await screen.findByRole("table", { hidden: true });
    const rows = table.querySelectorAll("tr.kchart-row");
    expect(rows).toHaveLength(history.points.length);
    expect(rows[0]?.textContent).toMatch(/6 de noviembre de 2026.*34\.311,68/);
    const months = [...table.querySelectorAll("tr.kchart-month")].map((r) => r.textContent);
    expect(months).toEqual(["noviembre de 2026", "octubre de 2026"]);
  });

  it("dice si hubo aportaciones en el periodo", async () => {
    stubApi({ ...history, net_flows_eur: "300.00" });
    renderChart();
    expect(await screen.findByText(/Incluye aportaciones por/)).toBeTruthy();
    expect(screen.getByText(/300,00/)).toBeTruthy();
  });

  it("sin datos explica que no se puede mostrar, sin cifras inventadas", async () => {
    stubApi({ code: "PRICE_UNAVAILABLE", message: "No hay precios." }, 503);
    renderChart();
    expect(await screen.findByText(/no podemos mostrar la evolución/)).toBeTruthy();
    expect(screen.queryByText(/€/)).toBeNull();
  });
});

describe("formato de los ejes", () => {
  it("fechas cortas en periodos cortos y mes y año desde un año", () => {
    expect(tickDate("2026-10-06T00:00:00Z", "1m")).toMatch(/6 oct/);
    expect(tickDate("2025-10-06T00:00:00Z", "max")).toMatch(/oct.*25/);
  });
  it("euros compactos en el eje Y", () => {
    expect(tickEur(34500)).toMatch(/34,5\s?mil\s?€/);
  });
  it("divisiones redondas del eje Y que cubren todos los valores", () => {
    expect(niceScale([23302.17, 44100])).toEqual({
      domain: [20000, 45000],
      ticks: [20000, 25000, 30000, 35000, 40000, 45000],
    });
    expect(niceScale([38167.17, 43900]).ticks).toEqual([38000, 40000, 42000, 44000]);
    const flat = niceScale([100, 100]).domain; // serie plana: dominio no vacío que la contiene
    expect(flat[0]).toBeLessThanOrEqual(100);
    expect(flat[1]).toBeGreaterThan(100);
  });
});
