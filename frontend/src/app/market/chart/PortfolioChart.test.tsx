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
    // La cifra es secundaria y va rotulada con su fecha y sin el impacto de los eventos.
    const label = await screen.findByText(
      /Valor al cierre del 6 de noviembre de 2026, sin el impacto estimado de los eventos/,
    );
    // Debajo, en una línea: valor al empezar y aportaciones.
    const line = label.nextElementSibling;
    expect(line?.textContent).toMatch(/Al empezar el periodo: 33\.410,25.*Aportaciones: \+300,00/);
    // Encima, el valor del último cierre y su variación respecto al anterior, con signo.
    expect(label.previousElementSibling?.textContent).toMatch(/34\.311,68.*−228,39/);
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("/portfolios/laura/history?period=1y");
    expect(screen.getByRole("radio", { name: "Último año" })).toHaveProperty("checked", true);
  });

  it("ofrece 1 semana, 1 mes, 6 meses, 1 año y todo", async () => {
    stubApi();
    renderChart();
    await screen.findByText(/Valor al cierre del/);
    const names = screen.getAllByRole("radio").map((r) => r.getAttribute("aria-label"));
    expect(names).toEqual(["Última semana", "Último mes", "Últimos 6 meses", "Último año", "Todo el historial"]);
  });

  it("cambiar de periodo pide la serie de ese periodo", async () => {
    const fetchMock = stubApi();
    renderChart();
    await screen.findByText(/Valor al cierre del/);
    fireEvent.click(screen.getByRole("radio", { name: "Última semana" }));
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([url]) => String(url).includes("period=1w"))).toBe(true),
    );
    expect(screen.getByRole("radio", { name: "Última semana" })).toHaveProperty("checked", true);
  });

  it("pliega la escala de tiempo, la leyenda y la tabla en «Ajustar vista»", async () => {
    stubApi();
    renderChart();
    const adjust = await screen.findByRole("button", { name: "Ajustar vista" });
    expect(adjust.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByRole("button", { name: "Mostrar leyenda" })).toBeNull();
    expect(screen.queryByText(/^Ver tabla/)).toBeNull();
    fireEvent.click(adjust);
    expect(adjust.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByRole("button", { name: "Mostrar leyenda" })).toBeTruthy();
    expect(screen.getByText(/^Ver tabla/)).toBeTruthy();
    fireEvent.click(adjust);
    expect(screen.queryByText(/^Ver tabla/)).toBeNull();
  });

  it("tiene una tabla alternativa con todos los puntos, agrupados por mes y del más reciente", async () => {
    stubApi();
    renderChart();
    fireEvent.click(await screen.findByRole("button", { name: "Ajustar vista" }));
    const summary = await screen.findByText(/^Ver tabla/);
    expect(screen.queryByRole("table", { hidden: true })).toBeNull(); // plegada: sin filas
    const details = summary.closest("details") as HTMLDetailsElement;
    details.open = true;
    fireEvent(details, new Event("toggle"));
    const table = await screen.findByRole("table", { hidden: true });
    const rows = table.querySelectorAll("tr.kchart-row");
    expect(rows).toHaveLength(history.points.length);
    // Del más reciente: valor y variación con signo; la aportación, en su etiqueta.
    expect(rows[0]?.textContent).toMatch(/6 de noviembre de 2026.*34\.311,68.*−228,39.*\(−0,66\s%\)/);
    expect(rows[3]?.textContent).toMatch(/\+447,32.*Aportación \+300,00/);
    // Fondo suave según la variación: ganancia, pérdida o sin variación (el primero).
    expect([...rows].map((r) => r.getAttribute("data-trend"))).toEqual(["down", "down", "up", "up", "up", "flat"]);
    expect(rows[5]?.textContent).toMatch(/—/); // el primero no tiene variación
    const months = [...table.querySelectorAll("tr.kchart-month")].map((r) => r.textContent);
    expect(months).toEqual(["Noviembre de 2026", "Octubre de 2026"]);
  });

  it("explica cómo leer la gráfica con una leyenda plegable", async () => {
    stubApi();
    renderChart();
    fireEvent.click(await screen.findByRole("button", { name: "Ajustar vista" }));
    const toggle = await screen.findByRole("button", { name: "Mostrar leyenda" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByRole("heading", { name: "Cómo leer la gráfica" })).toBeNull(); // oculta
    fireEvent.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    expect(toggle.textContent).toBe("Ocultar leyenda");
    const heading = screen.getByRole("heading", { name: "Cómo leer la gráfica" });
    const items = heading.nextElementSibling?.querySelectorAll("li") ?? [];
    const text = [...items].map((li) => li.textContent).join(" | ");
    expect(text).toMatch(/Por encima del valor inicial.*Por debajo del valor inicial.*Línea dorada.*Zonas sombreadas.*Punto azul.*Escala de fechas/);
  });

  it("sin aportaciones lo dice en la línea de datos", async () => {
    stubApi({ ...history, net_flows_eur: "0.00" });
    renderChart();
    expect(await screen.findByText("Sin aportaciones ni retiradas en el periodo.")).toBeTruthy();
  });

  it("de dónde sale: una pista breve al pasar por la cifra, sin abrir nada", async () => {
    stubApi();
    renderChart();
    await screen.findByText(/Valor al cierre del/);
    const [hint] = screen.getAllByRole("tooltip", { hidden: true });
    expect(hint?.textContent).toMatch(/participaciones × precio de cierre.*Precios de cierre de 1 activo y tipo de cambio/);
    const figure = hint?.parentElement;
    expect(figure?.getAttribute("tabindex")).toBe("0");
    expect(figure?.getAttribute("aria-describedby")).toBe(hint?.id);
    expect(figure?.getAttribute("data-calc-id")).toBe(history.calc_id);
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
    // «1A» con solo unas semanas de datos: el día, no «oct 26» repetido.
    expect(tickDate("2026-10-06T00:00:00Z", "1y", 30)).toMatch(/6 oct/);
    expect(tickDate("2025-10-06T00:00:00Z", "1y", 365)).toMatch(/oct.*25/);
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
